# providers.py
# shared helper for importing and configuring transcription providers

import importlib


def configure_provider(provider, app_settings):
    """Import the provider module and apply per-provider settings."""
    module = importlib.import_module(provider)
    configure = getattr(module, "configure", None)
    if configure:
        if provider == "whisper_local":
            configure(model_size=app_settings["whisper_model"])
        elif provider == "gemini_proxy":
            configure(model_chain=app_settings["gemini_models"])
        elif provider == "vosk_local":
            configure(model_overrides=app_settings.get("vosk_model_overrides") or {})
    return module
