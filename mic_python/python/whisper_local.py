# whisper_local.py
# local transcription using faster-whisper (multilingual, offline)

import sys
import logging
from pathlib import Path

from faster_whisper import WhisperModel
from languages import LANGUAGES

try:
    from faster_whisper.tokenizer import _LANGUAGE_CODES
    _WHISPER_LANGS = set(_LANGUAGE_CODES)
except Exception:  # pragma: no cover - fallback if internals change
    _WHISPER_LANGS = None

logging.basicConfig(encoding="utf-8")

################################################################################################
# CONSTANTS
################################################################################################

ROOT_DIR = Path(getattr(sys, "frozen", False) and sys.executable or __file__).resolve().parent
DEFAULT_MODEL_SIZE = "small"  # multilingual, best speed/accuracy balance for CPU

VALID_SIZES = ("tiny", "tiny.en", "base", "base.en", "small", "small.en",
               "medium", "medium.en", "large-v3-turbo")

# English-only variants perform better on English audio (same size/speed).
# Used automatically when the app language is English. No other language has
# dedicated whisper models.
EN_VARIANTS = {"tiny": "tiny.en", "base": "base.en",
               "small": "small.en", "medium": "medium.en"}

################################################################################################
# MODEL LOADING (cached per model name - load once, reuse for every transcription)
################################################################################################

_models = {}
_model_size = None
_prefer_en_variant = True
_progress = None  # optional callback(message, current_mb, total_mb_or_None)

# approximate download sizes (MB) for first-run hints
_SIZE_HINTS_MB = {
    "tiny": 75, "tiny.en": 75, "base": 145, "base.en": 145,
    "small": 490, "small.en": 490, "medium": 1500, "medium.en": 1500,
    "large-v3-turbo": 1600,
}


def _report(message, current=None, total=None):
    if _progress:
        try:
            _progress(message, current, total)
        except Exception:
            pass


def configure(model_size=None, prefer_en_variant=None, progress=None):
    """Set the model size / English-variant behavior / progress callback."""
    global _model_size, _prefer_en_variant, _progress
    if model_size in VALID_SIZES:
        _model_size = model_size
    if prefer_en_variant is not None:
        _prefer_en_variant = prefer_en_variant
    if progress is not None:
        _progress = progress


def _current_size():
    return _model_size or DEFAULT_MODEL_SIZE


def _resolve_size(lang):
    size = _current_size()
    if _prefer_en_variant and lang == "en" and size in EN_VARIANTS:
        return EN_VARIANTS[size]
    return size


def get_model(lang=None):
    name = _resolve_size(lang)
    if name in _models:
        _report(f"whisper '{name}' already loaded", None, None)
        return _models[name]
    label = (f"{name} (English variant of '{_current_size()}')"
             if name != _current_size() else name)
    if name in _SIZE_HINTS_MB:
        _report(f"loading whisper '{label}' (downloads ~{ _SIZE_HINTS_MB[name]} MB on first use)...",
                0, _SIZE_HINTS_MB[name])
    else:
        _report(f"loading whisper '{label}'...", None, None)
    logging.info("Loading faster-whisper model '%s' (first run downloads it)...", label)
    try:
        model = WhisperModel(name, compute_type="int8", device="cpu")
    except Exception as e:
        logging.error("Failed to load whisper model '%s': %s", name, e)
        logging.error("Check your internet connection (models download once from Hugging Face)")
        logging.error("or try a smaller model size in the mic app menu")
        raise
    _models[name] = model
    _report(f"whisper '{name}' ready", None, None)
    logging.info("faster-whisper '%s' loaded.", name)
    return model


################################################################################################
# TRANSCRIPTION
################################################################################################

def _normalize_lang(lang):
    """Map accent/region codes to base languages whisper understands (en-gb -> en)."""
    if lang and "-" in lang:
        base = lang.split("-", 1)[0]
        if _WHISPER_LANGS is None or base in _WHISPER_LANGS:
            return base
    return lang


def transcribe_audio_file(audio_path: str,
                          prompt: str,
                          lang: str = "en",
                          out_path: str | None = None) -> str:
    """Transcribe audio using local faster-whisper model.

    NOTE: initial_prompt only helps when it matches the audio language.
    Whisper has no translation for arbitrary prompts, so it is passed
    only for English audio and skipped otherwise to avoid degrading output.
    """
    lang = _normalize_lang((lang or "").lower())
    model = get_model(lang)
    supported = _WHISPER_LANGS if _WHISPER_LANGS is not None else set(LANGUAGES)
    if lang not in supported:
        logging.warning("Language '%s' is not supported by whisper, falling back to auto-detect.", lang)
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
    logging.info("Transcription from %s: %s", detected, text)

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
        logging.error("Local whisper unavailable: %s", e)
        logging.error("Try: pip install faster-whisper")


################################################################################################
# GPT STUB
################################################################################################

def ask_gpt(question: str, model: str) -> str:
    return "This function is not available in local-only mode."
