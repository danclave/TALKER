# proxy_common.py
# shared machinery for transcription via the LLM-API-Key-Proxy
# (chat completions endpoint, OpenAI-compatible, inline base64 audio)

import base64
import logging

import requests

from languages import LANGUAGES

PROXY_URL = "http://127.0.0.1:8000/v1/chat/completions"
PROXY_API_KEY = "VerysecretKey"

REQUEST_TIMEOUT_S = 300


def _instruction(prompt: str, lang: str) -> str:
    language_name = LANGUAGES.get((lang or "").lower(), lang)
    instruction = f"Transcribe the following audio. The language is {language_name}."
    if prompt:
        instruction += f" For context, here is a hint about the content: '{prompt}'."
    instruction += (" Return only the transcribed text, without any additional "
                    "comments or formatting.")
    return instruction


def transcribe_via_proxy(model_chain, audio_path, prompt, lang, out_path=None):
    """Send audio to the proxy, trying each model in order until one succeeds.

    model_chain: ordered list of 'provider/modelname' strings (proxy format).
    Returns the transcription text ('' when every model failed).
    """
    if not model_chain:
        logging.error("No models configured for the proxy provider.")
        print("[ERROR] No models configured - add at least one model first.")
        return ""

    with open(audio_path, "rb") as audio_file:
        audio_bytes = audio_file.read()
    logging.info("Read %d bytes from %s", len(audio_bytes), audio_path)
    encoded_data = base64.b64encode(audio_bytes).decode("utf-8")

    headers = {
        "Authorization": f"Bearer {PROXY_API_KEY}",
        "Content-Type": "application/json",
    }

    base_payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": _instruction(prompt, lang)},
                    {
                        "type": "file",
                        "file": {
                            "file_data": f"data:audio/ogg;base64,{encoded_data}"
                        },
                    },
                ],
            }
        ],
        "thinking": {"type": "enabled", "budget_tokens": -1},
    }

    last_error = None
    for model in model_chain:
        payload = dict(base_payload)
        payload["model"] = model
        try:
            logging.info("Trying model '%s'...", model)
            response = requests.post(PROXY_URL, headers=headers, json=payload,
                                     timeout=REQUEST_TIMEOUT_S)
            response.raise_for_status()
            transcription = (response.json()
                             .get("choices", [{}])[0]
                             .get("message", {})
                             .get("content", ""))
            if transcription.strip():
                print(f"Transcription from {model}: {transcription}")
                if out_path:
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(transcription)
                return transcription
            logging.warning("Model '%s' returned an empty transcription, trying next...", model)
            last_error = RuntimeError(f"'{model}' returned empty result")
        except requests.exceptions.RequestException as e:
            logging.warning("Model '%s' failed: %s", model, e)
            if e.response is not None:
                logging.warning("Response body: %s", e.response.text)
            last_error = e
        except Exception as e:
            logging.warning("Model '%s' failed unexpectedly: %s", model, e)
            last_error = e

    logging.error("All models failed. Last error: %s", last_error)
    print(f"[ERROR] Transcription failed for all models: {' -> '.join(model_chain)}")
    return ""


def check_proxy(timeout=8):
    """True when the proxy answers /v1/models with our key."""
    try:
        base = PROXY_URL.rsplit("/v1/", 1)[0]
        response = requests.get(base + "/v1/models",
                                headers={"Authorization": f"Bearer {PROXY_API_KEY}"},
                                timeout=timeout)
        return response.status_code == 200
    except Exception as e:
        logging.info("Proxy check failed: %s", e)
        return False
