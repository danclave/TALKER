# vosk_local.py
# ultra-light offline transcription using Vosk (~40 MB per language model)
# models are downloaded once from alphacephei.com and cached next to the app

import io
import json
import logging
import sys
import zipfile
from pathlib import Path

import numpy as np
import requests
import soundfile as sf

from languages import vosk_model_info, vosk_model_url, vosk_model_is_big, LANGUAGES
from vosk import KaldiRecognizer, Model as VoskModel, SetLogLevel

logging.basicConfig(encoding="utf-8")

SetLogLevel(-1)  # silence kaldi internals

################################################################################################
# CONSTANTS
################################################################################################

ROOT_DIR = Path(getattr(sys, "frozen", False) and sys.executable or __file__).resolve().parent
MODELS_DIR = ROOT_DIR / "vosk_models"
SAMPLE_RATE = 16000
FALLBACK_LANG = "en"  # used when the selected language has no Vosk model

_model = None
_model_lang = None

################################################################################################
# MODEL LOADING (singleton)
################################################################################################

def _download_model(model_name: str, url: str, size_mb: int) -> Path:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    target_dir = MODELS_DIR / model_name
    # archives from alphacephei extract to a folder named exactly like the model
    if target_dir.is_dir() and any(target_dir.iterdir()):
        return target_dir

    print(f"Downloading Vosk model '{model_name}' (~{size_mb} MB, one time)...")
    if size_mb >= 150:
        print("[WARN] This is a large model - it will use more resources and be slow.")
    try:
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        zip_bytes = response.content
    except Exception as e:
        print(f"[ERROR] Model download failed: {e}")
        print(f"-> Check your internet connection, or download manually from {url}")
        raise

    print("Extracting model...")
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            zf.extractall(MODELS_DIR)
    except Exception as e:
        print(f"[ERROR] Model extraction failed: {e}")
        raise
    if not target_dir.is_dir():
        raise RuntimeError(f"Unexpected model archive layout in {MODELS_DIR}")
    return target_dir


def get_model(lang: str = FALLBACK_LANG):
    global _model, _model_lang
    if _model is not None and _model_lang == lang:
        return _model

    use_lang = lang if vosk_model_info(lang) else FALLBACK_LANG
    if use_lang != lang:
        print(f"[WARN] No Vosk model for '{lang}' "
              f"({LANGUAGES.get(lang, lang)}), falling back to English. "
              f"Consider the Whisper provider for this language.")

    model_name, size_mb = vosk_model_info(use_lang)
    url = vosk_model_url(use_lang)
    model_dir = _download_model(model_name, url, size_mb)
    _model = VoskModel(str(model_dir))
    _model_lang = use_lang
    print(f"[OK] Vosk model '{model_name}' loaded.")
    return _model


################################################################################################
# AUDIO DECODING (any input format -> 16k mono PCM16)
################################################################################################

def _decode_audio(audio_path: str) -> bytes:
    data, rate = sf.read(audio_path, dtype="float64", always_2d=True)

    if data.shape[1] > 1:
        data = data.mean(axis=1)

    if rate != SAMPLE_RATE:
        # linear resample - input from our recorder is already 16k, this is a safety net
        duration = len(data) / rate
        target_len = max(1, int(duration * SAMPLE_RATE))
        data = np.interp(
            np.linspace(0.0, 1.0, target_len, endpoint=False) * (len(data) - 1),
            np.arange(len(data)),
            data,
        )

    pcm = np.clip(data, -1.0, 1.0)
    return (pcm * 32767.0).astype(np.int16).tobytes()


################################################################################################
# TRANSCRIPTION
################################################################################################

def transcribe_audio_file(audio_path: str,
                          prompt: str,
                          lang: str = "en",
                          out_path: str | None = None) -> str:
    """Transcribe audio using a local Vosk model (prompt is ignored - not supported)."""
    try:
        model = get_model((lang or "").lower())
        pcm = _decode_audio(audio_path)

        recognizer = KaldiRecognizer(model, SAMPLE_RATE)
        recognizer.SetWords(False)

        chunk = 4096
        for i in range(0, len(pcm), chunk):
            recognizer.AcceptWaveform(pcm[i:i + chunk])
        final = json.loads(recognizer.FinalResult())

        text = final.get("text", "").strip()
        print(f"Transcription from {_model_lang}: {text}")

        if out_path:
            Path(out_path).write_text(text, encoding="utf-8")
        return text

    except Exception as e:
        logging.error("Vosk transcription failed: %s", e)
        return ""


################################################################################################
# API KEY HANDLING (noop)
################################################################################################

def load_openai_api_key():
    test_transcription_service()


def test_transcription_service():
    try:
        get_model(FALLBACK_LANG)
    except Exception as e:
        print(f"[ERROR] Vosk unavailable: {e}")
        print("-> Try: pip install vosk")


def ask_gpt(question: str, model: str) -> str:
    return "This function is not available in local-only mode."
