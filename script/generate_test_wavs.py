"""Generate test WAV files using Home Assistant."""

import argparse
import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Union
from urllib.request import Request, urlopen

from ruamel.yaml import YAML

from speech_to_phrase.lang_sentences import LanguageData

_DIR = Path(__file__).parent
_REPO_DIR = _DIR.parent
_STP_DIR = _REPO_DIR / "speech_to_phrase"
_SENTENCES_DIR = _STP_DIR / "sentences"
_TESTS_DIR = _REPO_DIR / "tests"
_FIXTURES_DIR = _TESTS_DIR / "fixtures"
_TEST_SENTENCES_DIR = _TESTS_DIR / "sentences"
_BACKGROUND_NOISE_WAV = _TESTS_DIR / "wav" / "background_noise.wav"

_LOGGER = logging.getLogger(__name__)

TTS_LANG = {
    "en": "en-US",
    "el": "el-GR",
    "cs": "cs-CZ",
    "ca": "ca-ES",
    "pt_PT": "pt-PT",
    "hi": "hi-IN",
    "eu": "eu-ES",
    "fa": "fa-IR",
    "sk": "sk-SK",
    "sl": "sl-SI",
    "sw": "sw-KE",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hass-url", default="http://localhost:8123")
    parser.add_argument("--hass-token", required=True)
    parser.add_argument("--engine", default="tts.home_assistant_cloud")
    parser.add_argument(
        "--output-dir", default=_TESTS_DIR / "wav", help="Path to output directory"
    )
    parser.add_argument("--language", help="Only generate WAV files for language")
    parser.add_argument(
        "--delete", action="store_true", help="Delete unneeded WAV files"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    output_dir = Path(args.output_dir)

    if not shutil.which("sox"):
        _LOGGER.fatal("sox must be installed")
        return 1

    yaml = YAML(typ="safe")
    slot_lists: dict[str, list[str]] = {
        "brightness": ["10", "20", "100"],
        "seconds": ["10", "15", "100"],
        "minutes": ["2", "20", "45", "100"],
        "hours": ["2", "24"],
    }

    for sentences_path in _SENTENCES_DIR.glob("*.yaml"):
        language = sentences_path.stem

        if args.language and (language != args.language):
            continue

        tts_language = TTS_LANG.get(language, f"{language}-{language.upper()}")

        lang_wav_dir = output_dir / language
        lang_gen_wav_dir = lang_wav_dir / "generated"
        lang_gen_wav_dir.mkdir(parents=True, exist_ok=True)

        lang_slot_lists = dict(slot_lists)

        with open(sentences_path, "r", encoding="utf-8") as sentences_file:
            sentences_dict = yaml.load(sentences_file)

        lang_data = LanguageData.from_dict(sentences_dict)
        for list_name, list_values in lang_data.list_values.items():
            if list_name not in lang_slot_lists:
                lang_slot_lists[list_name] = list_values

        # Add test fixtures
        fixtures_path = _FIXTURES_DIR / f"{language}.yaml"
        with open(fixtures_path, "r", encoding="utf-8") as fixtures_file:
            fixtures_dict = yaml.load(fixtures_file)["fixtures"]

        if "areas" in fixtures_dict:
            lang_slot_lists["area"] = [
                name for a in fixtures_dict["areas"] for name in coerce_list(a["name"])
            ]

        if "floors" in fixtures_dict:
            lang_slot_lists["floor"] = [
                name for a in fixtures_dict["floors"] for name in coerce_list(a["name"])
            ]

        for list_name, list_values in fixtures_dict.get("lists", {}).items():
            if list_name not in lang_slot_lists:
                lang_slot_lists[list_name] = list_values

        # Load test sentences
        test_sentences_path = _TEST_SENTENCES_DIR / f"{language}.yaml"
        with open(test_sentences_path, "r", encoding="utf-8") as test_sentences_file:
            test_sentences_dict = yaml.load(test_sentences_file)

        test_sentences = test_sentences_dict["sentences"]

        generated_wav_names: set[str] = set()
        for sentence_info in sentences_dict["data"]:
            if isinstance(sentence_info, str):
                sentence_info = {"sentences": [sentence_info]}

            name_domains = sentence_info.get("domains", [])
            if name_domains:
                sen_slot_lists = {
                    **lang_slot_lists,
                    "name": [
                        name
                        for e in fixtures_dict["entities"]
                        for name in coerce_list(e["name"])
                        if e["domain"] in name_domains
                    ],
                }
            else:
                sen_slot_lists = dict(lang_slot_lists)

            lang_data.add_transformed_lists(sen_slot_lists)

            for sentence in test_sentences:
                wav_path = lang_wav_dir / f"{sentence}.wav"
                gen_wav_path = lang_gen_wav_dir / f"{sentence}.wav"
                generated_wav_names.add(sentence)

                if wav_path.exists() or gen_wav_path.exists():
                    continue

                generate_wav(
                    args.hass_url,
                    args.hass_token,
                    args.engine,
                    tts_language,
                    sentence,
                    gen_wav_path,
                )
                print(wav_path)

        if args.delete:
            for gen_wav_path in lang_gen_wav_dir.glob("*.wav"):
                if gen_wav_path.stem in generated_wav_names:
                    continue

                gen_wav_path.unlink()
                print("DELETED:", gen_wav_path)

    return 0


def coerce_list(str_or_list: Union[str, list[str]]) -> list[str]:
    if isinstance(str_or_list, str):
        return [str_or_list]

    return str_or_list


# -----------------------------------------------------------------------------


def generate_wav(
    hass_url: str,
    hass_token: str,
    engine: str,
    language: str,
    text: str,
    wav_path: Path,
) -> None:
    request = Request(
        f"{hass_url}/api/tts_get_url",
        data=json.dumps(
            {"engine_id": engine, "message": text, "language": language}
        ).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {hass_token}",
        },
    )
    with urlopen(request) as response:
        audio_url = json.load(response)["url"]

    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        wav_no_noise = temp_dir / "no_noise.wav"
        wav_bg_noise = temp_dir / "bg_noise.wav"

        with urlopen(audio_url) as response:
            subprocess.check_call(
                [
                    "sox",
                    "-t",
                    "mp3",
                    "-",
                    "-r",
                    "16000",
                    "-c",
                    "1",
                    "-e",
                    "signed-integer",
                    "-b",
                    "16",
                    "-t",
                    "wav",
                    str(wav_no_noise),
                    "lowpass",
                    "5000",
                    "highpass",
                    "200",
                    "reverb",
                    "50",
                    "50",
                    "100",
                    "pad",
                    "0.2",
                ],
                stdin=response,
            )

        wav_duration = (
            subprocess.check_output(["soxi", "-D", str(wav_no_noise)]).decode().strip()
        )

        # Add background noise
        subprocess.check_call(
            [
                "sox",
                str(_BACKGROUND_NOISE_WAV),
                str(wav_bg_noise),
                "vol",
                "2",
                "trim",
                "0",
                wav_duration,
            ]
        )
        subprocess.check_call(
            [
                "sox",
                "-m",
                str(wav_bg_noise),
                str(wav_no_noise),
                "-b",
                "16",
                str(wav_path),
            ]
        )


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    main()
