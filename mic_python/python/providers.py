# providers.py
# shared helper for importing, configuring and pre-loading transcription providers

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


def prepare_model(app_settings):
    """Download/load the selected model BEFORE it is needed (test or first use).

    Returns True when the provider is ready, False on failure (logged, non-fatal).
    """
    provider = app_settings["provider"]
    lang = app_settings.get("language", "en")
    try:
        if provider == "vosk_local":
            import vosk_local
            vosk_local.get_model(lang)
        elif provider == "whisper_local":
            import whisper_local
            whisper_local.get_model(lang)
        elif provider == "gemini_proxy":
            import requests
            from gemini_proxy import PROXY_URL, PROXY_API_KEY
            base = PROXY_URL.rsplit("/v1/", 1)[0]
            requests.get(base + "/v1/models",
                         headers={"Authorization": f"Bearer {PROXY_API_KEY}"},
                         timeout=10).raise_for_status()
            print("[OK] Proxy reachable.")
        return True
    except Exception as e:
        print(f"[WARN] Could not prepare {provider}: {e}")
        return False
