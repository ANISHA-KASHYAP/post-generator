"""Small helper for talking to a local Ollama server."""

import requests

OLLAMA_URL = "http://localhost:11434"
TIMEOUT_SECONDS = 180


class OllamaError(Exception):
    """Raised when Ollama cannot be reached or returns an error."""


def list_models():
    """Return installed model names, or None if Ollama is not running."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        response.raise_for_status()
    except requests.RequestException:
        return None

    data = response.json()
    return [model["name"] for model in data.get("models", [])]


def generate_post(prompt, model="llama3.2:3b", temperature=0.8):
    """Send one prompt to Ollama and return the generated text."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": 700,
        },
    }

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=TIMEOUT_SECONDS,
        )
    except requests.exceptions.ConnectionError:
        raise OllamaError(
            "Could not connect to Ollama. Run `ollama serve` in a terminal, then try again."
        ) from None
    except requests.exceptions.Timeout:
        raise OllamaError(
            "Ollama took too long to answer. Try a shorter post or run it again."
        ) from None

    if response.status_code != 200:
        raise OllamaError(
            f"Ollama returned an error ({response.status_code}): {response.text[:200]}"
        )

    text = response.json().get("response", "").strip()
    if not text:
        raise OllamaError("Ollama returned an empty response. Please try again.")

    return text
