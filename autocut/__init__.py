__version__ = "1.1.0"

from .type import LANG, WhisperModel, WhisperMode
from .utils import load_audio

__all__ = ["Transcribe", "load_audio", "WhisperMode", "WhisperModel", "LANG"]


def __getattr__(name):
    if name == "Transcribe":
        from .package_transcribe import Transcribe

        return Transcribe
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
