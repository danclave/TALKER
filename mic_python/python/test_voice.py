import sys

from mic_test import run_test
from settings import load_settings

# --- Configuration ---
# Optional CLI args: test_voice.py [provider] [model]
#   - provider: whisper_local | vosk_local | gemini_proxy | whisper_api
#   - model:    whisper size (tiny/base/small/...) or gemini model string


def main():
    app_settings = load_settings()
    if len(sys.argv) > 1 and sys.argv[1]:
        app_settings["provider"] = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2]:
        if app_settings["provider"] == "whisper_local":
            app_settings["whisper_model"] = sys.argv[2]
        elif app_settings["provider"] == "gemini_proxy":
            app_settings["gemini_models"] = [sys.argv[2]]

    run_test(app_settings)


if __name__ == '__main__':
    main()
