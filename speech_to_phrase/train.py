"""Model training."""

import argparse
import asyncio
import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

from hassil import Intents, merge_dict

from .const import Settings, TrainingError, WordCasing
from .g2p import LexiconDatabase
from .hass_api import Things
from .hassil_fst import Fst, G2PInfo, intents_to_fst
from .lang_sentences import LanguageData, load_shared_lists
from .models import MODELS, Model, ModelType, download_model
from .train_coqui_stt import train_coqui_stt
from .train_kaldi import train_kaldi
from .util import quote_strings, yaml, yaml_output

_LOGGER = logging.getLogger(__name__)


@dataclass
class TrainingInfo:
    """Information used to determine if training is required."""

    model_version: str
    sentences_hash: str
    things_hash: str


async def train(
    model: Model, settings: Settings, things: Things, force_retrain: bool = False
) -> None:
    """Train a speech model.

    If the model does not exist, it will be downloaded.
    If the previous training information is identical, training will be skipped.
    """
    model_dir = settings.model_data_dir(model.id)
    if not model_dir.exists():
        await download_model(model, settings)

    training_info = TrainingInfo(
        model_version=model.version,
        sentences_hash=_get_sentences_hash(model, settings),
        things_hash=things.get_hash(),
    )

    training_info_path = settings.model_training_info_path(model.id)
    if (not force_retrain) and training_info_path.exists():
        with open(training_info_path, "r", encoding="utf-8") as training_info_file:
            last_training_info = TrainingInfo(**json.load(training_info_file))

        if last_training_info == training_info:
            _LOGGER.debug("Skipping training of %s", model.id)
            return

    _LOGGER.info("Started training: %s", model.id)
    train_dir = settings.model_train_dir(model.id).absolute()
    train_dir.mkdir(parents=True, exist_ok=True)

    # Written at the end of training
    training_info_path.unlink(missing_ok=True)

    # Create intents
    intents = _create_intents(model, settings, things)
    if intents is {}:
        if model.type == ModelType.KALDI:
            lexicon = LexiconDatabase(settings.models_dir / model.id / "lexicon.db")
            fst = _create_intents_fst(model, lexicon, intents)
            await train_kaldi(model, settings, lexicon, fst)
        elif model.type == ModelType.COQUI_STT:
            lexicon = LexiconDatabase()
            fst = _create_intents_fst(model, lexicon, intents)
            await train_coqui_stt(model, settings, fst)
        else:
            raise TrainingError(f"Unexpected model type for {model.id}: {model.type}")


        # Write training info
        with open(training_info_path, "w", encoding="utf-8") as training_info_file:
            json.dump(
                asdict(training_info),
                training_info_file,
            )

        _LOGGER.info("Finished training: %s", model.id)
    else:
        _LOGGER.warning("Nothing to train. Add intents and retrain.")


# -----------------------------------------------------------------------------


def _create_intents(model: Model, settings: Settings, things: Things) -> Intents:
    """Create intents from sentences and things from Home Assistant."""

    sentences_path = settings.sentences / f"{model.sentences_language}.yaml"
    sentences_dict = {}
    sentences_dict["language"] = model.sentences_language
    lang_data = LanguageData.from_dict(sentences_dict)
    if not settings.skip_pre_defined_templates:
        with open(sentences_path, "r", encoding="utf-8") as sentences_file:
            lang_data = LanguageData.from_dict(yaml.load(sentences_file))
            sentences_dict = lang_data.to_intents_dict()

    
        
    lists_dict = sentences_dict.get("lists", {})
    lists_dict.update(things.to_lists_dict())

    with open(settings.shared_lists_path, "r", encoding="utf-8") as shared_lists_file:
        shared_lists_dict = load_shared_lists(yaml.load(shared_lists_file))
        lists_dict.update(shared_lists_dict)

    sentences_dict["lists"] = lists_dict

    # Sentence triggers, ask_question answers, etc.
    if things.extra_sentences:
        intents_dict = sentences_dict.get("intents", {})
        intents_dict["ExtraSentences"] = {
            "data": [{"sentences": things.extra_sentences}]
        }
        sentences_dict["intents"] = intents_dict

    # Custom sentences
    for custom_sentences_dir in settings.custom_sentences_dirs:
        dir_for_language = custom_sentences_dir / model.language
        if not dir_for_language.is_dir():
            # Try language family
            dir_for_language = custom_sentences_dir / model.language_family

            if not dir_for_language.is_dir():
                continue

        for custom_sentences_path in sorted(dir_for_language.glob("*.yaml")):
            _LOGGER.debug("Loading custom sentences from %s", custom_sentences_path)

            with open(
                custom_sentences_path, "r", encoding="utf-8"
            ) as custom_sentences_file:
                merge_dict(sentences_dict, yaml.load(custom_sentences_file) or {})

    # Clean up lists that were wildcards but now have values
    for list_info in lists_dict.values():
        if "values" in list_info:
            list_info.pop("wildcard", None)

    lang_intents = Intents.from_dict(sentences_dict)
    tr_lists = lang_data.add_transformed_slot_lists(lang_intents.slot_lists)

    # Write YAML with training sentences (includes HA lists, triggers, etc.)
    training_sentences_path = settings.training_sentences_path(model.id)
    with open(
        training_sentences_path, "w", encoding="utf-8"
    ) as training_sentences_file:
        # Add transformed lists to debug YAML
        for tr_list_name, tr_list in tr_lists.items():
            lists_dict[tr_list_name] = {
                "values": [
                    {
                        "in": value.value_out,
                        "out": value.value_out,
                        "context": value.context or {},
                        "metadata": value.metadata or {},
                    }
                    for value in tr_list.values
                ]
            }
        yaml_output.dump(quote_strings(sentences_dict), training_sentences_file)

    _LOGGER.debug("Wrote debug YAML to %s", training_sentences_path)

    return lang_intents


def _create_intents_fst(
    model: Model, lexicon: LexiconDatabase, intents: Intents
) -> Fst:
    """Create a finite state transducer (FST) directly from intents.

    This allows for efficiently generating an n-gram language model using
    opengrm instead of enumerating all possible sentences.
    """
    casing_func = WordCasing.get_function(model.casing)

    fst = intents_to_fst(
        intents,
        number_language=model.number_language,
        g2p_info=G2PInfo(lexicon, casing_func),
    ).remove_spaces()

    # Remove dead branches
    fst.prune()

    return fst


def _get_sentences_hash(
    model: Model, settings: Settings, chunk_size: int = 8192
) -> str:
    """Get a hash of sentences YAML files (builtin and custom)."""
    hasher = hashlib.sha256()

    # Builtin sentences
    if not settings.skip_pre_defined_templates:
        sentences_path = settings.sentences / f"{model.sentences_language}.yaml"
        with open(sentences_path, "rb") as sentences_file:
            chunk = sentences_file.read(chunk_size)
            hasher.update(chunk)

    # Custom sentences
    for custom_sentences_dir in settings.custom_sentences_dirs:
        dir_for_language = custom_sentences_dir / model.language
        if not dir_for_language.is_dir():
            # Try language family
            dir_for_language = custom_sentences_dir / model.language_family

            if not dir_for_language.is_dir():
                continue

        for custom_sentences_path in sorted(dir_for_language.glob("*.yaml")):
            with open(custom_sentences_path, "rb") as custom_sentences_file:
                chunk = custom_sentences_file.read(chunk_size)
                hasher.update(chunk)

    return hasher.hexdigest()


# -----------------------------------------------------------------------------


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model", required=True, help="Id of speech model (e.g., en_US-rhasspy)"
    )
    parser.add_argument(
        "--sentences",
        required=True,
        action="append",
        help="Path to sentences YAML file",
    )
    parser.add_argument(
        "--train-dir", required=True, help="Directory to write trained model files"
    )
    parser.add_argument(
        "--tools-dir", required=True, help="Directory with kaldi, openfst, etc."
    )
    parser.add_argument(
        "--models-dir", required=True, help="Directory with speech models"
    )
    parser.add_argument("--debug", action="store_true", help="Log DEBUG messages")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    _LOGGER.debug(args)

    model = next(iter(m for m in MODELS.values() if m.id == args.model), None)
    assert model is not None, f"Unknown model id: {args.model}"

    settings = Settings(
        models_dir=Path(args.models_dir),
        train_dir=Path(args.train_dir),
        tools_dir=Path(args.tools_dir),
        custom_sentences_dirs=[],
        hass_token="",
        hass_websocket_uri="",
        retrain_on_connect=False,
    )

    intents = Intents.from_files(args.sentences)

    if model.type == ModelType.KALDI:
        lexicon = LexiconDatabase(settings.models_dir / model.id / "lexicon.db")
        fst = _create_intents_fst(model, lexicon, intents)
        await train_kaldi(model, settings, lexicon, fst)
    else:
        raise TrainingError(f"Unexpected model type for {model.id}: {model.type}")

    _LOGGER.info("Trained %s", settings.train_dir)


if __name__ == "__main__":
    asyncio.run(main())
