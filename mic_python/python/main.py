import os
from pathlib import Path
import sys
import time
import logging
import tempfile

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from files import read_file, write_to_file
from recorder import Recorder
from banner import print_banner
from providers import configure_provider, prepare_model
import mic_test

import settings as settings_module

# Make console output crash-proof on non-UTF-8 consoles (cp1251/cp1252):
# unencodable characters (emoji, foreign text) become '?' instead of raising.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except Exception:
        pass

####################################################################################################
# CONFIG
####################################################################################################

# Logging: file always; console handler is added only for non-TUI modes
# (in the TUI, diagnostics go to the in-app LOG pane instead - F12).
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("talker.log", encoding="utf-8"),  # persistent log
    ],
)


def _enable_console_logging():
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logging.getLogger().addHandler(console)

# Get the system's temporary directory
TEMP_DIR = tempfile.gettempdir()

# File paths in the temporary directory
COMMAND_FILE = os.path.join(TEMP_DIR, 'talker_mic_io_commands')
TRANSCRIPTION_FILE = os.path.join(TEMP_DIR, 'talker_mic_io_transcription')
AUDIO_FILE = os.path.join(TEMP_DIR, 'talker_audio.ogg')

# Commands
COMMANDS = {
    'LISTENING': 'LISTENING',
    'TRANSCRIBING': 'TRANSCRIBING',
    'START'       : 'START-',   # syntax: START-<lang>-<prompt>
    'STOP': 'STOP',
    'DONE': 'DONE',
    'ERROR': 'ERROR'
}


####################################################################################################
# STARTUP CONFIG RESOLUTION
####################################################################################################

def resolve_startup_config():
    """Decide provider/model/language for this session.

    - CLI provider argument (legacy/advanced): bypass the menu entirely.
      Optional 2nd argument overrides the whisper size or gemini model.
    - Otherwise: always show the interactive menu, prefilled from settings.
    """
    app_settings = settings_module.load_settings()

    if len(sys.argv) > 1 and sys.argv[1] in settings_module.VALID_PROVIDERS:
        app_settings["provider"] = sys.argv[1]
        if len(sys.argv) > 2 and sys.argv[2]:
            if app_settings["provider"] == "whisper_local" and sys.argv[2] in settings_module.WHISPER_MODELS:
                app_settings["whisper_model"] = sys.argv[2]
            elif app_settings["provider"] == "gemini_proxy":
                app_settings["gemini_models"] = [sys.argv[2]]
            elif app_settings["provider"] == "custom_proxy":
                app_settings["custom_models"] = [sys.argv[2]]
        _enable_console_logging()  # CLI users get console diagnostics
        return app_settings

    # Full TUI for interactive terminals; plain menu fallback for piped stdin.
    if sys.stdin.isatty() and sys.stdout.isatty():
        try:
            import tui
        except Exception as e:
            print(f"[WARN] TUI unavailable ({e}), falling back to the plain menu.")
            _enable_console_logging()
        else:
            app_settings = tui.run_tui(app_settings, on_test=mic_test.run_test)
            return app_settings

    _enable_console_logging()
    app_settings, _ = settings_module.run_menu(app_settings, on_test=mic_test.run_test)
    return app_settings


####################################################################################################
# MAIN
####################################################################################################

def main():
    observer = None
    try:
        print("-"*50)
        print_banner("TALKER")
        print("-"*50)

        app_settings = resolve_startup_config()
        provider = app_settings["provider"]
        app_language = app_settings["language"]  # app setting always wins over game-sent lang

        transcription_module = configure_provider(provider, app_settings)
        load_api_key = getattr(transcription_module, "load_openai_api_key")
        transcribe_audio_file_func = getattr(transcription_module, "transcribe_audio_file")
        load_api_key()
        # download/cache the selected model up front so the first in-game
        # use does not stall on a download (progress printed to console)
        prepare_model(app_settings, report=lambda msg, cur, tot: print(
            f"  {msg}" + (f"  [{cur}/{tot} MB]" if tot else "")))
        recorder = Recorder(AUDIO_FILE)
        Path(COMMAND_FILE).touch()

        handler  = CommandHandler(recorder, transcribe_audio_file_func, app_language)
        observer = Observer()
        observer.schedule(handler, TEMP_DIR, recursive=False)
        observer.start()

        logging.info("Observer running, watching %s", COMMAND_FILE)
        print(f"Provider: {provider} | Language: {app_language}")
        print("You can now use the in-game key to talk.")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logging.info("User interrupt.")
    except SystemExit:
        raise
    except Exception:
        logging.exception("Unhandled error.")
    finally:
        try:
            if observer is not None:
                observer.stop(); observer.join()
        except Exception:
            pass
        logging.info("Shutdown complete.")


####################################################################################################
# START COMMAND
####################################################################################################

def parse_start_line(line: str):
    """Extract (lang, prompt) from 'START-...'.

    The game sends 'START-<lang>-<prompt>' where <lang> may be empty ('START--<prompt>').
    The parsed language is informational only - the app's configured language always wins.
    """
    payload = line[len(COMMANDS['START']):]          # after START-
    if len(payload) >= 3 and payload[2] == '-':
        lang = payload[:2]
        prompt = payload[3:]
    elif payload.startswith('-'):                    # empty language: START--<prompt>
        lang = None
        prompt = payload[1:]
    else:
        lang = None
        prompt = payload
    return lang, prompt


####################################################################################################
# COMMAND HANDLER
####################################################################################################
class CommandHandler(FileSystemEventHandler):
    def __init__(self, recorder: Recorder, transcribe_func, app_language: str):
        self.recorder = recorder
        self.transcribe_func = transcribe_func
        self.app_language = app_language

    def on_modified(self, event):
        try:
            if os.path.abspath(event.src_path) == os.path.abspath(COMMAND_FILE):
                self._handle_command()
        except Exception as e:
            logging.warning("Error handling update: %s", e)

    # ─────────────── core ────────────────
    def _handle_command(self):
        raw = read_file(COMMAND_FILE)
        if raw.startswith(COMMANDS['START']):
            lang, prompt = parse_start_line(raw)
            self._record_session(prompt, lang)
        elif raw.strip() == COMMANDS['STOP']:
            self.recorder.stop_recording()

    def _record_session(self, prompt: str = '', language: str | None = None):
        try:
            write_to_file(COMMAND_FILE, COMMANDS['LISTENING'])
            self.recorder.start_recording()
            while self.recorder.is_recording():
                time.sleep(0.1)

            write_to_file(COMMAND_FILE, COMMANDS['TRANSCRIBING'])
            # the app's configured language always wins over what the game sent
            text = self.transcribe_func(AUDIO_FILE, prompt=prompt, lang=self.app_language)
            write_to_file(TRANSCRIPTION_FILE, text)
            write_to_file(COMMAND_FILE, COMMANDS['DONE'])

        except Exception as e:
            logging.error("Recording session failed: %s", e)
            write_to_file(COMMAND_FILE, COMMANDS['ERROR'])



if __name__ == '__main__':
    main()
