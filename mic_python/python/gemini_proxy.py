# gemini_proxy.py
# transcription via the LLM-API-Key-Proxy using Gemini voice-capable models
# models are tried in order (fallback chain): if one fails, the next is used

import requests
import logging
import base64

from languages import LANGUAGES

# The proxy URL for chat completions
PROXY_URL = "http://127.0.0.1:8000/v1/chat/completions"
PROXY_API_KEY = "VerysecretKey"

# Static list of voice-capable Gemini models (newest first).
# Update this list rarely, when Google retires or ships new lite models.
GEMINI_VOICE_MODELS = [
    "gemini/gemini-3.5-flash-lite",
    "gemini/gemini-3.1-flash-lite",
]

DEFAULT_MODEL_CHAIN = [
    "gemini/gemini-3.5-flash-lite",
    "gemini/gemini-3.1-flash-lite",
]

_model_chain = list(DEFAULT_MODEL_CHAIN)


def configure(model_chain=None):
    """Set the fallback chain of models (called by main from settings/CLI)."""
    global _model_chain
    if isinstance(model_chain, list) and model_chain:
        _model_chain = [m for m in model_chain if isinstance(m, str) and m]


def _current_chain():
    return _model_chain or list(DEFAULT_MODEL_CHAIN)


def transcribe_audio_file(audio_path: str, prompt: str, lang: str = "en", out_path: str | None = None) -> str:
    """
    Transcribe audio using the proxy by sending it to the chat completions endpoint.
    Tries each configured model in order until one succeeds.
    """
    language_name = LANGUAGES.get((lang or "").lower(), lang)

    # Dynamically construct the prompt
    instruction = f"Transcribe the following audio. The language is {language_name}."
    if prompt:
        instruction += f" For context, here is a hint about the content: '{prompt}'."
    instruction += " Return only the transcribed text, without any additional comments or formatting."

    # 1. Read audio file and encode it in base64
    with open(audio_path, "rb") as audio_file:
        audio_bytes = audio_file.read()
    logging.info(f"Read {len(audio_bytes)} bytes from {audio_path}")
    encoded_data = base64.b64encode(audio_bytes).decode("utf-8")
    logging.info(f"Base64 encoded data length: {len(encoded_data)}")

    # 2. Prepare the request payload
    headers = {
        "Authorization": f"Bearer {PROXY_API_KEY}",
        "Content-Type": "application/json"
    }

    base_payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": instruction},
                    {
                        "type": "file",
                        "file": {
                            "file_data": f"data:audio/ogg;base64,{encoded_data}"
                        }
                    }
                ]
            }
        ],
        "thinking": {"type": "enabled", "budget_tokens": -1}
    }

    # 3. Try each model in the fallback chain
    last_error = None
    for model in _current_chain():
        payload = dict(base_payload)
        payload["model"] = model

        try:
            logging.info(f"Trying model '{model}'...")
            response = requests.post(PROXY_URL, headers=headers, json=payload)
            response.raise_for_status()

            response_json = response.json()
            transcription = response_json.get("choices", [{}])[0].get("message", {}).get("content", "")

            if transcription.strip():
                print(f"Transcription from Gemini ({model}): {transcription}")

                if out_path:
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(transcription)

                return transcription

            logging.warning(f"Model '{model}' returned an empty transcription, trying next model...")
            last_error = RuntimeError(f"'{model}' returned empty result")

        except requests.exceptions.RequestException as e:
            logging.warning(f"Model '{model}' failed: {e}")
            if e.response is not None:
                logging.warning(f"Response body: {e.response.text}")
            last_error = e
        except Exception as e:
            logging.warning(f"Model '{model}' failed unexpectedly: {e}")
            last_error = e

    # 4. All models failed
    logging.error(f"All Gemini models failed. Last error: {last_error}")
    print(f"[ERROR] Transcription failed for all models: {' -> '.join(_current_chain())}")
    return ""


def load_openai_api_key():
    """
    This function is a placeholder to maintain compatibility with the existing main script.
    No API key loading is needed when using the proxy.
    """
    print("Using proxy for transcription. No API key needed.")
    pass
