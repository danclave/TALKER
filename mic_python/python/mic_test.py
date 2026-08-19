# mic_test.py
# live microphone transcription test using the currently selected settings
# used by the mic app menu ("Test transcription") and by test_voice.py

import sys
import time

# Make console output crash-proof on non-UTF-8 consoles
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except Exception:
        pass

from recorder import Recorder
from providers import configure_provider, prepare_model

AUDIO_FILE = "talker_test_audio.ogg"
GRACE_SECONDS = 5


def run_test(app_settings):
    """Record from the mic and transcribe with the selected provider/settings."""
    provider = app_settings["provider"]
    module = configure_provider(provider, app_settings)
    transcribe = getattr(module, "transcribe_audio_file")

    print()
    print("-" * 50)
    print(f"Live test | provider: {provider} | language: {app_settings['language']}")
    if provider == "whisper_local":
        print(f"Whisper model: {app_settings['whisper_model']}")
    elif provider == "gemini_proxy":
        print(f"Gemini chain: {' -> '.join(app_settings['gemini_models'])}")
    print("-" * 50)

    print("Preparing model (downloads and caches on first use)...")
    if not prepare_model(app_settings):
        print("Model/proxy not ready - transcription may fail.")

    recorder = Recorder(AUDIO_FILE)
    print(f"Speak now (recording starts immediately, stops after ~2s of silence)...")
    t0 = time.perf_counter()
    recorder.start_recording(silence_grace_period=GRACE_SECONDS)
    while recorder.is_recording():
        time.sleep(0.1)
    record_seconds = time.perf_counter() - t0

    print("Transcribing...")
    t1 = time.perf_counter()
    text = transcribe(AUDIO_FILE, prompt="", lang=app_settings["language"])
    transcribe_seconds = time.perf_counter() - t1

    print()
    print(f"Recorded {record_seconds:.1f}s | transcription took {transcribe_seconds:.1f}s")
    if text:
        print(f"Heard: {text}")
    else:
        print("Heard: (nothing - empty transcription)")
    print("-" * 50)
