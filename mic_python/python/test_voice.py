import sys
import time
import os

# Make console output crash-proof on non-UTF-8 consoles
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except Exception:
        pass

from recorder import Recorder
from settings import load_settings
from main import configure_provider

# --- Configuration ---
AUDIO_FILE = 'talker_test_audio.ogg'  # Save in the same directory as the script
RECORD_SECONDS = 5


def main():
    """
    Records a short audio clip and transcribes it with the configured provider.
    Optional CLI args: test_voice.py [provider] [model]
      - provider: whisper_local | vosk_local | gemini_proxy | whisper_api
      - model:    whisper size (tiny/base/small/...) or gemini model string
    """
    app_settings = load_settings()
    if len(sys.argv) > 1 and sys.argv[1]:
        app_settings["provider"] = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2]:
        if app_settings["provider"] == "whisper_local":
            app_settings["whisper_model"] = sys.argv[2]
        elif app_settings["provider"] == "gemini_proxy":
            app_settings["gemini_models"] = [sys.argv[2]]

    print(f"--- Voice Transcription Test ({app_settings['provider']}) ---")

    module = configure_provider(app_settings["provider"], app_settings)
    transcribe_audio_file = getattr(module, "transcribe_audio_file")

    # 1. Record audio
    recorder = Recorder(AUDIO_FILE)
    print(f"Recording with a {RECORD_SECONDS}-second silence grace period...")
    print(f"Say something in '{app_settings['language']}'...")
    recorder.start_recording(silence_grace_period=RECORD_SECONDS)

    # In this test, we will manually stop the recording after the grace period
    # to ensure a predictable test duration.
    print(f"Waiting for {RECORD_SECONDS + 1} seconds before stopping...")
    time.sleep(RECORD_SECONDS + 1)  # Record for grace period + 1 second
    if recorder.is_recording():
        recorder.stop_recording()

    print(f"Recording finished. Audio saved to: {os.path.abspath(AUDIO_FILE)}")

    # 2. Transcribe audio
    print("Transcribing audio...")
    transcription = transcribe_audio_file(AUDIO_FILE, prompt="", lang=app_settings["language"])

    # 3. Print result
    if transcription:
        print("\n--- Transcription Result ---")
        print(transcription)
    else:
        print("\n--- Transcription Failed ---")
        print("No transcription received. Check the logs for errors.")


if __name__ == '__main__':
    main()
