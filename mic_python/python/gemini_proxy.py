# gemini_proxy.py
# transcription via the LLM-API-Key-Proxy using Gemini voice-capable models
# (shared proxy machinery lives in proxy_common.py)
# NOTE: requires the API proxy running with Gemini API key(s) configured.

import logging

from proxy_common import transcribe_via_proxy

# Static list of voice-capable Gemini models (newest first).
# Update this list rarely, when Google retires or ships new lite models.
GEMINI_VOICE_MODELS = [
    "gemini/gemini-3.5-flash-lite",
    "gemini/gemini-3.1-flash-lite",
]

DEFAULT_MODEL_CHAIN = list(GEMINI_VOICE_MODELS)

_model_chain = list(DEFAULT_MODEL_CHAIN)


def configure(model_chain=None):
    """Set the fallback chain of models (called by main from settings/CLI)."""
    global _model_chain
    if isinstance(model_chain, list) and model_chain:
        _model_chain = [m for m in model_chain if isinstance(m, str) and m]


def transcribe_audio_file(audio_path: str, prompt: str, lang: str = "en",
                          out_path: str | None = None) -> str:
    """Transcribe audio through the proxy, trying each model in order."""
    return transcribe_via_proxy(_model_chain, audio_path, prompt, lang, out_path)


def load_openai_api_key():
    logging.info("Using proxy for transcription. No direct API key needed.")
    print("Using the proxy for transcription. It needs Gemini API key(s) configured.")
