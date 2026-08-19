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


def run_test(app_settings, status=None, stop_requested=None, on_recording=None,
             on_level=None):
    """Record from the mic and transcribe with the selected provider/settings.

    status:         callable(str) receiving live progress lines (default: print)
    stop_requested: callable() -> bool - stop recording early when it returns True
    on_recording:   callable(bool) - fired with True when recording starts,
                    False when it ends (for visual indicators)
    on_level:       callable(level_pct, silence_remaining, elapsed) - fired
                    ~20x/s while recording, for the live audio level meter.
                    level_pct: 0-100 normalized so the silence threshold is 50.
                    silence_remaining: seconds until silence auto-stop (None
                    when the input is above the threshold).
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

    silence_level = app_settings.get("silence_level", 1000)
    recorder = Recorder(AUDIO_FILE,
                        silence_level=silence_level,
                        device=app_settings.get("input_device"),
                        gain=app_settings.get("mic_gain", 1.0))
    say("recording... speak now")
    say("(silence countdown starts as soon as you stop talking; stops "
        "itself if you never speak)")
    if on_recording:
        on_recording(True)
    t0 = time.perf_counter()

    def _tick():
        if on_level is None:
            return
        try:
            level = recorder.get_level() or 0.0
            # normalize: silence threshold sits at 50% of the meter
            pct = min(100, int(100 * level / max(1, silence_level * 2)))
            remaining = recorder.get_silence_remaining()
            clip = recorder.is_clipping()
            on_level(pct, remaining, time.perf_counter() - t0, clip)
        except Exception:
            pass

    # first-speech arming: silence before you speak never counts toward the
    # auto-stop countdown; if you never speak, it stops after 10s total
    recorder.start_recording(arm_on_speech=True, no_speech_timeout=10.0)
    try:
        while recorder.is_recording():
            _tick()
            if stop_requested and stop_requested():
                recorder.stop_recording()
                say("stop requested - recording ended")
                break
            time.sleep(0.05)
        _tick()
    finally:
        if on_recording:
            on_recording(False)
    record_seconds = time.perf_counter() - t0

    # optional: play the recording back (parallel with transcription)
    if app_settings.get("playback_after"):
        from recorder import play_audio_file
        play_audio_file(AUDIO_FILE)
        say("playing back your recording...")

    say("transcribing...")
    t1 = time.perf_counter()
    text = transcribe(AUDIO_FILE, prompt="", lang=app_settings["language"])
    transcribe_seconds = time.perf_counter() - t1

    say(f"recorded {record_seconds:.1f}s | transcription took {transcribe_seconds:.1f}s")
    say(f"heard: {text}" if text else "heard: (nothing - empty transcription)")
    return text
