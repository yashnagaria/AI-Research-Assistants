import os

from llm_client import get_client
from utils.logger import api_logger

client = get_client()

def get_embedding(text: str, model: str = None):
    """
    Get embedding vector for text using the configured provider
    """
    if model is None:
        model = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")

    api_logger.debug(f"🔢 Generating embedding - Model: {model}, Text length: {len(text)} chars")

    response = client.embeddings.create(
        input=text,
        model=model
    )

    # Not every provider reports usage on embeddings (Gemini returns none)
    usage = getattr(response, "usage", None)
    if usage is not None:
        api_logger.debug(f"✅ Embedding generated | Tokens: {usage.total_tokens}")

    return response.data[0].embedding

def call_openai(prompt: str, model: str = None):
    """
    Generic chat completion wrapper for agents
    """
    if model is None:
        model = os.getenv("LLM_MODEL", "gemini-3.6-flash")

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
