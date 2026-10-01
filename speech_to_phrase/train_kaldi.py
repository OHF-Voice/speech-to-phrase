"""Model training for Kaldi."""

import gzip
import hashlib
import logging
import shlex
import shutil
import tempfile
from pathlib import Path
from typing import Set

from .const import EPS, SIL, SPN, UNK, Settings
from .g2p import LexiconDatabase
from .hassil_fst import Fst
from .models import Model
from .speech_tools import SpeechTools

_LOGGER = logging.getLogger(__name__)


async def train_kaldi(
    model: Model, settings: Settings, lexicon: LexiconDatabase, fst: Fst
) -> None:
    """Train a Kaldi speech model."""
    model_dir = (settings.model_data_dir(model.id) / "model").absolute()
    train_dir = settings.model_train_dir(model.id).absolute()
    train_dir.mkdir(parents=True, exist_ok=True)

    # Copy conf
    conf_dir = train_dir / "conf"
    if conf_dir.exists():
        shutil.rmtree(conf_dir)

    shutil.copytree(model_dir / "conf", conf_dir)

    # Delete existing data/graph
    data_dir = train_dir / "data"
    if data_dir.exists():
        shutil.rmtree(data_dir)

    for graph_dir in train_dir.glob("graph_*"):
        if graph_dir.is_dir():
            continue

        shutil.rmtree(graph_dir)

    # ---------------------------------------------------------------------
    # Kaldi Training
    # ---------------------------------------------------------
    # 1. prepare_lang.sh
    # 2. format_lm.sh (or fstcompile)
    # 3. mkgraph.sh
    # 4. prepare_online_decoding.sh
    # ---------------------------------------------------------

    # Create empty path.sh
    path_sh = train_dir / "path.sh"
    if not path_sh.is_file():
        path_sh.write_text("")

    # Write pronunciation dictionary
    await _create_lexicon(
        fst, lexicon, model_dir, train_dir, settings.tools, spn_phone=model.spn_phone
    )

    # Create utils link
    model_utils_link = train_dir / "utils"
    model_utils_link.unlink(missing_ok=True)
    model_utils_link.symlink_to(settings.tools.egs_utils_dir, target_is_directory=True)

    # 1. prepare_lang.sh
    await _prepare_lang(train_dir, settings.tools)

    # 2. Generate G.fst from skill graph
    await _create_arpa(fst, train_dir, settings.tools, method=model.arpa_method)
    await _create_fuzzy_fst(fst, train_dir, settings.tools)

    # 3. mkgraph.sh
    await _mkgraph(model_dir, train_dir, settings.tools)

    # 4. prepare_online_decoding.sh
    await _prepare_online_decoding(model_dir, train_dir, settings.tools)


# -----------------------------------------------------------------------------


async def _create_lexicon(
    fst: Fst,
    lexicon: LexiconDatabase,
    model_dir: Path,
    train_dir: Path,
    tools: SpeechTools,
    spn_phone: str = SPN,
) -> None:
    """Generate pronunciation dictionary."""
    _LOGGER.debug("Generating lexicon")
    data_local_dir = train_dir / "data" / "local"
    dict_local_dir = data_local_dir / "dict"
    dict_local_dir.mkdir(parents=True, exist_ok=True)

    # Copy phones
    phones_dir = model_dir / "phones"
    for phone_file in phones_dir.glob("*.txt"):
        shutil.copy(phone_file, dict_local_dir / phone_file.name)

    # Create dictionary
    dictionary_path = dict_local_dir / "lexicon.txt"
    with open(dictionary_path, "w", encoding="utf-8") as dictionary_file:
        missing_words = set()
        for word in sorted(fst.words):
            if word in (UNK,):
                continue

            word_found = False
            for word_pron in lexicon.lookup(word):
                phonemes_str = " ".join(word_pron)
                print(word, phonemes_str, file=dictionary_file)
                word_found = True

            if not word_found:
                missing_words.add(word)

        missing_words_path = train_dir / "missing_words_dictionary.txt"
        missing_words_path.unlink(missing_ok=True)

        if missing_words:
            g2p_model_path = model_dir.parent / "g2p.fst"
            with tempfile.NamedTemporaryFile(
                mode="w+", suffix=".txt", encoding="utf-8"
            ) as missing_words_file, open(
                missing_words_path, "w", encoding="utf-8"
            ) as missing_dictionary_file:
                for word in sorted(missing_words):
                    _LOGGER.warning("Guessing pronunciation for %s", word)
                    print(word, file=missing_words_file)

                missing_words_file.seek(0)
                phonetisaurus_output = (
                    (
                        await tools.async_run(
                            str(tools.phonetisaurus_bin),
                            [
                                f"--model={g2p_model_path}",
                                f"--wordlist={missing_words_file.name}",
                            ],
                        )
                    )
                    .decode()
                    .splitlines()
                )
                for line in phonetisaurus_output:
                    line = line.strip()
                    if line:
                        line_parts = line.split()
                        if len(line_parts) == 2:
                            word = line_parts[0]
                            _LOGGER.warning(
                                "No pronunciation could be guessed for: '%s'", word
                            )
                            print(word, SIL, file=dictionary_file)
                            continue

                        if len(line_parts) < 3:
                            continue

                        word = line_parts[0]
                        phonemes = " ".join(line_parts[2:])

                        print(
                            word,
                            phonemes,
                            file=missing_dictionary_file,
                        )
                        print(word, phonemes, file=dictionary_file)

        # Add <unk>
        print(UNK, spn_phone, file=dictionary_file)

        meta_labels = fst.output_words - fst.words
        for label in meta_labels:
            print(label, SIL, file=dictionary_file)


async def _prepare_lang(train_dir: Path, tools: SpeechTools) -> None:
    """Prepare data directory for language model."""
    data_dir = train_dir / "data"
    lang_dir = data_dir / "lang"
    data_local_dir = data_dir / "local"
    dict_local_dir = data_local_dir / "dict"
    lang_local_dir = data_local_dir / "lang"

    await tools.async_run(
        "bash",
        [
            str(tools.egs_utils_dir / "prepare_lang.sh"),
            str(dict_local_dir),
            UNK,
            str(lang_local_dir),
            str(lang_dir),
        ],
        cwd=train_dir,
    )


async def _create_arpa(
    fst: Fst,
    train_dir: Path,
    tools: SpeechTools,
    order: int = 3,
    method: str = "kneser_ney",
) -> None:
    """Create n-gram language model from intents."""
    data_dir = train_dir / "data"
    lang_dir = data_dir / "lang"
    data_local_dir = data_dir / "local"
    dict_local_dir = data_local_dir / "dict"
    lang_local_dir = data_local_dir / "lang"

    fst_path = lang_dir / "G.arpa.fst"
    text_fst_path = fst_path.with_suffix(".fst.txt")
    arpa_path = lang_dir / "lm.arpa"

    with open(text_fst_path, "w", encoding="utf-8") as text_fst_file:
        fst.write(text_fst_file)

    await tools.async_run(
        "fstcompile",
        [
            shlex.quote(f"--isymbols={lang_dir}/words.txt"),
            shlex.quote(f"--osymbols={lang_dir}/words.txt"),
            "--keep_isymbols=true",
            "--keep_osymbols=true",
            shlex.quote(str(text_fst_path)),
            shlex.quote(str(fst_path)),
        ],
    )
    await tools.async_run_pipeline(
        [
            "ngramcount",
            f"--order={order}",
            shlex.quote(str(fst_path)),
            "-",
        ],
        [
            "ngrammake",
            f"--method={method}",
        ],
        [
            "ngramprint",
            "--ARPA",
            "-",
            shlex.quote(str(arpa_path)),
        ],
    )

    arpa_gz_path = lang_local_dir / "lm.arpa.gz"
    with open(arpa_path, "r", encoding="utf-8") as arpa_file, gzip.open(
        arpa_gz_path, "wt", encoding="utf-8"
    ) as arpa_gz_file:
        shutil.copyfileobj(arpa_file, arpa_gz_file)  # type: ignore[misc]

    await tools.async_run(
        "bash",
        [
            str(tools.egs_utils_dir / "format_lm.sh"),
            str(lang_dir),
            str(arpa_gz_path),
            str(dict_local_dir / "lexicon.txt"),
            str(lang_dir),
        ],
    )


async def _create_fuzzy_fst(fst: Fst, train_dir: Path, tools: SpeechTools) -> None:
    """Create FST to fuzzy match sentences and output names with exact casing, etc."""
    data_dir = train_dir / "data"
    lang_dir = data_dir / "lang"

    fst_path = lang_dir / "G.arpa.fst"
    text_fst_path = fst_path.with_suffix(".fst.txt")

    # Create a version of the FST with self loops that allow skipping words
    fuzzy_fst_path = lang_dir / "G.fuzzy.fst"
    text_fuzzy_fst_path = fuzzy_fst_path.with_suffix(".fst.txt")
    _LOGGER.debug("Creating fuzzy FST at %s", fuzzy_fst_path)

    states: Set[str] = set()

    # Copy transitions and add self loops
    with open(text_fst_path, "r", encoding="utf-8") as text_fst_file, open(
        text_fuzzy_fst_path, "w", encoding="utf-8"
    ) as text_fuzzy_fst_file:
        for line in text_fst_file:
            line = line.strip()
            if not line:
                continue

            # Copy transition without probability
            parts = line.split()
            print(*parts[:4], file=text_fuzzy_fst_file)

            state = line.split(maxsplit=1)[0]
            if state in states:
                continue

            states.add(state)

        # Create self loops
        for state in states:
            # No penalty for <eps>
            print(state, state, EPS, EPS, 0.0, file=text_fuzzy_fst_file)

            for word in fst.words:
                if word[0] in ("<", "_"):
                    # Skip meta words
                    continue

                # Penalty for word removal
                print(state, state, word, EPS, 1.0, file=text_fuzzy_fst_file)

    await tools.async_run_pipeline(
        [
            "fstcompile",
            shlex.quote(f"--isymbols={lang_dir}/words.txt"),
            shlex.quote(f"--osymbols={lang_dir}/words.txt"),
            "--keep_isymbols=true",
            "--keep_osymbols=true",
            shlex.quote(str(text_fuzzy_fst_path)),
            "-",
        ],
        [
            "fstarcsort",
            "--sort_type=ilabel",
            "-",
            shlex.quote(str(fuzzy_fst_path)),
        ],
    )


async def _mkgraph(model_dir: Path, train_dir: Path, tools: SpeechTools) -> None:
    """Generate HCLG.fst."""
    data_dir = train_dir / "data"
    lang_dir = data_dir / "lang"
    graph_dir = train_dir / "graph"

    await tools.async_run(
        "bash",
        [
            str(tools.egs_utils_dir / "mkgraph.sh"),
            "--self-loop-scale",
            "1.0",
            str(lang_dir),
            str(model_dir / "model"),
            str(graph_dir),
        ],
    )


async def _prepare_online_decoding(
    model_dir: Path, train_dir: Path, tools: SpeechTools
) -> None:
    """Enable streaming decoding."""
    data_dir = train_dir / "data"
    lang_dir = data_dir / "lang"

    extractor_dir = model_dir / "extractor"
    if not extractor_dir.is_dir():
        _LOGGER.debug("Extractor dir does not exist: %s", extractor_dir)
        return

    # Generate online.conf
    mfcc_conf = model_dir / "conf" / "mfcc_hires.conf"
    await tools.async_run(
        "bash",
        [
            str(
                tools.egs_steps_dir / "online" / "nnet3" / "prepare_online_decoding.sh"
            ),
            "--mfcc-config",
            str(mfcc_conf),
            str(lang_dir),
            str(extractor_dir),
            str(model_dir / "model"),
            str(model_dir / "online"),
        ],
        cwd=train_dir,
    )


# -----------------------------------------------------------------------------


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
