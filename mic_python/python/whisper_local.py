# whisper_local.py
# local transcription using faster-whisper (multilingual, offline)

import sys
import logging
from pathlib import Path

from faster_whisper import WhisperModel
from languages import LANGUAGES

logging.basicConfig(encoding="utf-8")

################################################################################################
# CONSTANTS
################################################################################################

ROOT_DIR = Path(getattr(sys, "frozen", False) and sys.executable or __file__).resolve().parent
DEFAULT_MODEL_SIZE = "small"  # multilingual, best speed/accuracy balance for CPU

VALID_SIZES = ("tiny", "base", "small", "medium", "large-v3-turbo")

################################################################################################
# MODEL LOADING (singleton - load once, reuse for every transcription)
################################################################################################

_model = None
_model_size = None


def configure(model_size=None):
    """Set the model size to use (called by main from settings/CLI)."""
    global _model_size
    if model_size in VALID_SIZES:
        _model_size = model_size


def _current_size():
    return _model_size or DEFAULT_MODEL_SIZE


def get_model():
    global _model
    if _model is not None:
        return _model
    size = _current_size()
    print(f"Loading faster-whisper model '{size}' (first run downloads it)...")
    try:
        _model = WhisperModel(size, compute_type="int8", device="cpu")
    except Exception as e:
        print(f"[ERROR] Failed to load model '{size}': {e}")
        print("-> Check your internet connection (models download once from Hugging Face)")
        print("-> or try a smaller model size in the mic app menu")
        raise
    print(f"[OK] faster-whisper '{size}' loaded.")
    return _model


################################################################################################
# TRANSCRIPTION
################################################################################################

def transcribe_audio_file(audio_path: str,
                          prompt: str,
                          lang: str = "en",
                          out_path: str | None = None) -> str:
    """Transcribe audio using local faster-whisper model.

    NOTE: initial_prompt only helps when it matches the audio language.
    Whisper has no translation for arbitrary prompts, so it is passed
    only for English audio and skipped otherwise to avoid degrading output.
    """
    model = get_model()

    if lang not in LANGUAGES:
        logging.warning("Unknown language code '%s', falling back to auto-detect.", lang)
        lang = None

    whisper_kwargs = {"language": lang}
    if prompt and lang == "en":
        whisper_kwargs["initial_prompt"] = prompt

    try:
        segments, info = model.transcribe(audio_path, **whisper_kwargs)
        text = "".join(segment.text for segment in segments).strip()
    except Exception as e:
        logging.error("Transcription failed: %s", e)
        text = ""

    detected = getattr(info, "language", None) if lang is None else lang
    print(f"Transcription from {detected}: {text}")

    if out_path:
        Path(out_path).write_text(text, encoding="utf-8")

    return text


################################################################################################
# API KEY HANDLING (noop)
################################################################################################

def load_openai_api_key():
    test_transcription_service()


################################################################################################
# CHECK SERVICE AVAILABILITY
################################################################################################

def test_transcription_service():
    try:
        get_model()
    except Exception as e:
        print(f"[ERROR] Local whisper unavailable: {e}")
        print("-> Try: pip install faster-whisper")


################################################################################################
# GPT STUB
################################################################################################

def ask_gpt(question: str, model: str) -> str:
    return "This function is not available in local-only mode."
