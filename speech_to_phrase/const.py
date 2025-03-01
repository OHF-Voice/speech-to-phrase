"""Constants."""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union

from .speech_tools import SpeechTools

# Kaldi
EPS = "<eps>"
SIL = "SIL"  # silence
SPN = "SPN"  # spoken noise
UNK = "<unk>"  # unknown

# Coqui STT
BLANK = "<blank>"
SPACE = "<space>"

# Audio
RATE = 16000  # hertz
WIDTH = 2  # bytes
CHANNELS = 1


class Language(str, Enum):
    """Available languages."""

    ENGLISH = "en"
    FRENCH = "fr"
    GERMAN = "de"
    DUTCH = "nl"
    SPANISH = "es"
    ITALIAN = "it"
    GREEK = "el"
    # RUSSIAN = "ru"  # need more sentences
    # CZECH = "cs"  # need more sentences
    # SLOVAK = "sk" # need more sentences


class Settings:
    """Speech-to-phrase settings."""

    def __init__(
        self,
        models_dir: Union[str, Path],
        train_dir: Union[str, Path],
        tools_dir: Union[str, Path],
        custom_sentences_dirs: List[Union[str, Path]],
        hass_token: str,
        hass_websocket_uri: str,
        retrain_on_connect: bool,
        sentences_dir: Optional[Union[str, Path]] = None,
        default_language: str = Language.ENGLISH.value,
        volume_multiplier: float = 1.0,
    ) -> None:
        """Initialize settings."""
        self.models_dir = Path(models_dir)
        self.train_dir = Path(train_dir)
        self.tools = SpeechTools.from_tools_dir(tools_dir)
        self.custom_sentences_dirs = [Path(d) for d in custom_sentences_dirs]
        self.hass_token = hass_token
        self.hass_websocket_uri = hass_websocket_uri
        self.retrain_on_connect = retrain_on_connect

        if not sentences_dir:
            # Builtin sentences
            sentences_dir = Path(__file__).parent / "sentences"

        self.sentences = Path(sentences_dir)
        self.default_language = default_language
        self.volume_multiplier = volume_multiplier

    def model_data_dir(self, model_id: str) -> Path:
        """Path to model data."""
        return self.models_dir / model_id

    def model_train_dir(self, model_id: str) -> Path:
        """Path to training artifacts for a model."""
        return self.train_dir / model_id

    def model_training_info_path(self, model_id: str) -> Path:
        """Path to training info file for a model."""
        return self.model_train_dir(model_id) / "training_info.json"

    def training_sentences_path(self, model_id: str) -> Path:
        """Path to YAML file with training sentences."""
        return self.model_train_dir(model_id) / "sentences.yaml"


@dataclass
class CachedTranscriber:
    """Transcription task and audio queue."""

    task: asyncio.Task
    audio_queue: "asyncio.Queue[Optional[bytes]]"


@dataclass
class State:
    """Application state."""

    settings: Settings
    """Application settings."""

    model_train_tasks: Dict[str, asyncio.Task] = field(default_factory=dict)
    """Training tasks for each model id."""

    model_train_tasks_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    """Lock for model_train_tasks."""

    cached_transcribers: Dict[str, CachedTranscriber] = field(default_factory=dict)
    """Transcription tasks/audio queues for each model id."""

    cached_transcriber_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    """Lock for cached_transcriber."""


class WordCasing(str, Enum):
    """Casing applied to text when training model."""

    KEEP = "keep"
    LOWER = "lower"
    UPPER = "upper"

    @staticmethod
    def get_function(casing: "WordCasing") -> Callable[[str], str]:
        """Get a Python function to apply casing."""
        if casing == WordCasing.LOWER:
            return str.lower

        if casing == WordCasing.UPPER:
            return str.upper

        return lambda s: s


class SpeechToPhraseError(Exception):
    """Base class for Speech-to-Phrase errors."""


class TrainingError(SpeechToPhraseError):
    """Error during training."""


class TranscribingError(SpeechToPhraseError):
    """Error during transcribing."""
