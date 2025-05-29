# whisper_api.py
# represents the transcription

import openai

def load_openai_api_key(API_KEY_PATH):
    """Load the OpenAI API key from a file."""
    try:
        with open(API_KEY_PATH, "r") as file:
            api_key = file.read().strip()
        if not api_key:
            raise ValueError("OpenAI API key is empty. Please enter your API key in 'openAi_API_KEY.key'.")
        openai.api_key = api_key
        test_key()
    except FileNotFoundError:
        raise ValueError(f"OpenAI API key file '{API_KEY_PATH}' not found.")

def transcribe_audio_file(audio_file_path: str, prompt: str) -> str:
    """Transcribe the audio file using OpenAI Whisper API."""
    print("Transcribing audio...")
    try: 
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file= open(audio_file_path, "rb"),
            prompt=prompt,
            language="uk",
        )
        text = transcript.text
        print(f"Transcription: {text}")
        return text
    except Exception as e:
        print(f"Transcription failed: {e}")
        return None

def test_key():
    # says hello world to gpt4o mini
    prompt = "Say 'Key succesfully loaded!' "
    print(ask_gpt(prompt, "gpt-4o-mini"))


def ask_gpt(question: str, model: str) -> str:
    chat_completion = openai.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": question,
            }
        ],
        model=model,
    )
    return chat_completion.choices[0].message.content