# custom_proxy.py
# advanced provider: user-defined chain of ANY audio-capable models on the
# LLM-API-Key-Proxy. Model format is 'provider/modelname' (what the proxy
# expects), e.g. gemini/gemini-3.5-flash-lite or openai/gpt-4o-audio-preview.
# NOTE: the model must support audio input, and your proxy must hold
# credentials for every provider you reference.

import logging

from proxy_common import transcribe_via_proxy

_model_chain = []


def configure(model_chain=None):
    """Set the fallback chain of custom models (called from settings)."""
    global _model_chain
    if isinstance(model_chain, list):
        _model_chain = [m for m in model_chain if isinstance(m, str) and m.strip()]


def transcribe_audio_file(audio_path: str, prompt: str, lang: str = "en",
                          out_path: str | None = None) -> str:
    return transcribe_via_proxy(_model_chain, audio_path, prompt, lang, out_path)


def load_openai_api_key():
    logging.info("Custom models go through the proxy - no direct API key needed here.")
    print("Custom models run via the proxy. Make sure it is running and has "
          "credentials for the providers you entered.")
