import os
import sys
import time
import logging
import tempfile

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from recorder import Recorder
from whisper_api import load_openai_api_key, transcribe_audio_file

# Configure logging
logging.basicConfig(level=logging.ERROR)

# Configuration
API_KEY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'openAi_API_KEY.key')

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
    'START': 'START-',
    'STOP': 'STOP',
    'DONE': 'DONE'
}

def main():
    """Main function to start the observer and handle commands."""
    # Load the OpenAI API key once
    load_openai_api_key(API_KEY_PATH)

    # Initialize the recorder
    recorder = Recorder(AUDIO_FILE)

    # Ensure the command file exists
    if not os.path.exists(COMMAND_FILE):
        open(COMMAND_FILE, 'w').close()

    # Set up the observer to watch for file changes
    event_handler = CommandHandler(recorder)
    observer = Observer()
    observer.schedule(event_handler, path=TEMP_DIR, recursive=False)
    observer.start()
    logging.debug(f"Observer started, watching for commands in {COMMAND_FILE}.")
    print("TALKER speech to text started. You can now activate it via the game key.")

    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    print("Exiting...")
    sys.exit(0)

class CommandHandler(FileSystemEventHandler):
    """Handles changes to the command file."""

    def __init__(self, recorder):
        self.recorder = recorder

    def on_modified(self, event):
        if os.path.abspath(event.src_path) == os.path.abspath(COMMAND_FILE):
            self.handle_command()

    def handle_command(self):
        content = read_file(COMMAND_FILE)
        if content.startswith(COMMANDS['START']):
            prompt = content[len(COMMANDS['START']):]
            self.start_recording_session(prompt)
        elif content.strip() == COMMANDS['STOP']:
            self.recorder.stop_recording()

    def start_recording_session(self, prompt=''):
        try:
            write_to_file(COMMAND_FILE, COMMANDS['LISTENING'])
            print("Recording started.")
            self.recorder.start_recording()

            # Wait until recording stops
            while self.recorder.is_recording():
                time.sleep(0.1)
            print("Recording complete.")

            # Transcribe the audio file
            write_to_file(COMMAND_FILE, COMMANDS['TRANSCRIBING'])
            transcription = transcribe_audio_file(AUDIO_FILE, prompt)
            write_to_file(TRANSCRIPTION_FILE, transcription)
            write_to_file(COMMAND_FILE, COMMANDS['DONE'])
        except Exception as e:
            if e == "Error querying device -1":
                logging.error(f"Error during recording. No input device found. Check the computer's current default input device.")
            else:
                logging.error(f"Error during recording session.{e}")
            write_to_file(COMMAND_FILE, 'ERROR')

def read_file(file_path):
    """Reads and returns the content of a file."""
    try:
        with open(file_path, 'r') as file:
            content = file.read().strip()
        return content
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        return ""

def write_to_file(file_path, content):
    """Writes content to a file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        logging.debug(f"Wrote '{content}' to {file_path}.")
    except Exception as e:
        logging.error(f"Error writing to file {file_path}: {e}")

if __name__ == '__main__':
    main()
