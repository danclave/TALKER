# mic_test.py
# live microphone transcription test using the currently selected settings
# used by both TUIs ("Test transcription") and by test_voice.py

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


def run_test(app_settings, status=None, stop_requested=None, on_recording=None):
    """Record from the mic and transcribe with the selected provider/settings.

    status:         callable(str) receiving live progress lines (default: print)
    stop_requested: callable() -> bool - stop recording early when it returns True
    on_recording:   callable(bool) - fired with True when recording starts,
                    False when it ends (for visual indicators)
    Returns the transcription text ('' on failure).
    """
    say = status or (lambda msg: print(msg))

    provider = app_settings["provider"]
    module = configure_provider(provider, app_settings)
    transcribe = getattr(module, "transcribe_audio_file")

    say(f"provider: {provider} | language: {app_settings['language']}")
    if provider == "whisper_local":
        say(f"whisper model: {app_settings['whisper_model']}")
    elif provider == "gemini_proxy":
        say(f"gemini chain: {' -> '.join(app_settings['gemini_models'])}")

    say("preparing model (downloads and caches on first use)...")

    def _report(message, current, total):
        if total:
            pct = int(100 * (current or 0) / total)
            say(f"  {message}  [{current}/{total} MB  {pct}%]")
        else:
            say(f"  {message}")

    if not prepare_model(app_settings, report=_report):
        say("[WARN] model/proxy not ready - transcription may fail")

    recorder = Recorder(AUDIO_FILE)
    say("recording... speak now (stops after ~2s of silence)")
    if on_recording:
        on_recording(True)
    t0 = time.perf_counter()
    recorder.start_recording(silence_grace_period=GRACE_SECONDS)
    try:
        while recorder.is_recording():
            if stop_requested and stop_requested():
                recorder.stop_recording()
                say("stop requested - recording ended")
                break
            time.sleep(0.1)
    finally:
        if on_recording:
            on_recording(False)
    record_seconds = time.perf_counter() - t0

    say("transcribing...")
    t1 = time.perf_counter()
    text = transcribe(AUDIO_FILE, prompt="", lang=app_settings["language"])
    transcribe_seconds = time.perf_counter() - t1

    say(f"recorded {record_seconds:.1f}s | transcription took {transcribe_seconds:.1f}s")
    say(f"heard: {text}" if text else "heard: (nothing - empty transcription)")
    return text
