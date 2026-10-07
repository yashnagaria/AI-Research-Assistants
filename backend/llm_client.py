"""Small, key-free client for Ollama's native local HTTP API."""
from __future__ import annotations

from typing import Iterable
from types import SimpleNamespace
import requests

from config import EMBEDDING_MODEL, LLM_MODEL, OLLAMA_BASE_URL, OLLAMA_TIMEOUT


class OllamaUnavailable(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = LLM_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def chat(self, messages: Iterable[dict[str, str]], temperature: float = 0.2) -> str:
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={"model": self.model, "messages": list(messages), "stream": False,
                      "options": {"temperature": temperature}},
                timeout=OLLAMA_TIMEOUT,
            )
            response.raise_for_status()
            return response.json()["message"]["content"].strip()
        except (requests.RequestException, KeyError, ValueError) as exc:
            raise OllamaUnavailable(
                f"Ollama is unavailable at {self.base_url}. Start 'ollama serve' and "
                f"run 'ollama pull {self.model}'."
            ) from exc

    def is_ready(self) -> bool:
        try:
            return requests.get(f"{self.base_url}/api/tags", timeout=3).ok
        except requests.RequestException:
            return False

    def embed(self, texts: list[str], model: str = EMBEDDING_MODEL) -> list[list[float]]:
        try:
            response = requests.post(
                f"{self.base_url}/api/embed",
                json={"model": model, "input": texts},
                timeout=OLLAMA_TIMEOUT,
            )
            if response.status_code != 404:
                response.raise_for_status()
                return response.json()["embeddings"]
            # Ollama versions before /api/embed accepted one prompt at a time.
            vectors = []
            for text in texts:
                legacy = requests.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": model, "prompt": text},
                    timeout=OLLAMA_TIMEOUT,
                )
                legacy.raise_for_status()
                vectors.append(legacy.json()["embedding"])
            return vectors
        except (requests.RequestException, KeyError, ValueError) as exc:
            raise OllamaUnavailable(
                f"Local embedding model is unavailable. Run 'ollama pull {model}'."
            ) from exc


ollama_client = OllamaClient()


class _CompletionsAdapter:
    """Temporary compatibility for the legacy /ask route."""
    def create(self, model=None, messages=None, temperature=0.2, **kwargs):
        content = ollama_client.chat(messages or [], temperature)
        usage = SimpleNamespace(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))], usage=usage)


def get_client():
    return SimpleNamespace(chat=SimpleNamespace(completions=_CompletionsAdapter()))
