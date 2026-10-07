"""Open-source embeddings served locally by Ollama."""
from config import EMBEDDING_MODEL
from llm_client import ollama_client


def get_embedding(text: str, model: str | None = None) -> list[float]:
    return ollama_client.embed([text], model or EMBEDDING_MODEL)[0]


def get_embeddings(texts: list[str], model: str | None = None, batch_size: int = 32) -> list[list[float]]:
    vectors: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        vectors.extend(ollama_client.embed(texts[start:start + batch_size], model or EMBEDDING_MODEL))
    return vectors
