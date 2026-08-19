# providers.py
# shared helper for importing, configuring and pre-loading transcription providers

import importlib


def configure_provider(provider, app_settings, progress=None):
    """Import the provider module and apply per-provider settings."""
    module = importlib.import_module(provider)
    configure = getattr(module, "configure", None)
    if configure:
        if provider == "whisper_local":
            configure(model_size=app_settings["whisper_model"], progress=progress)
        elif provider in ("gemini_proxy", "custom_proxy"):
            key = "custom_models" if provider == "custom_proxy" else "gemini_models"
            configure(model_chain=app_settings.get(key) or [])
        elif provider == "vosk_local":
            configure(model_overrides=app_settings.get("vosk_model_overrides") or {},
                      progress=progress)
    return module


def prepare_model(app_settings, report=None):
    """Download/load the selected model BEFORE it is needed (test or first use).

    report: optional callback(message, current_mb, total_mb_or_None) receiving
    download/load progress. Returns True when ready, False on failure.
    """
    provider = app_settings["provider"]
    lang = app_settings.get("language", "en")
    try:
        if provider == "vosk_local":
            import vosk_local
            vosk_local.configure(progress=report)
            vosk_local.get_model(lang)
        elif provider == "whisper_local":
            import whisper_local
            whisper_local.configure(progress=report)
            whisper_local.get_model(lang)
        elif provider in ("gemini_proxy", "custom_proxy"):
            import proxy_common
            if proxy_common.check_proxy():
                if report:
                    report("proxy reachable", None, None)
            else:
                if report:
                    report("proxy NOT reachable - is it running?", None, None)
                return False
        return True
    except Exception as e:
        print(f"[WARN] Could not prepare {provider}: {e}")
        return False
