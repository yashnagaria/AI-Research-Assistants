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

def get_embeddings(texts: list[str], model: str = None, batch_size: int = 100) -> list:
    """
    Embed many texts with one API request per batch instead of one per text.
    Falls back to per-text requests if the provider rejects list input.
    """
    if model is None:
        model = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")

    vectors = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        try:
            response = client.embeddings.create(input=batch, model=model)
            data = response.data
            # OpenAI sets `index` on each item; Gemini leaves it None but keeps input order
            if all(d.index is not None for d in data):
                data = sorted(data, key=lambda d: d.index)
            if len(data) != len(batch):
                raise ValueError(f"Expected {len(batch)} embeddings, got {len(data)}")
            vectors.extend(d.embedding for d in data)
        except Exception as e:
            api_logger.warning(f"Batch embedding failed ({e}), falling back to one request per chunk")
            vectors.extend(get_embedding(t, model) for t in batch)

    api_logger.info(f"✅ Embedded {len(texts)} texts in {-(-len(texts) // batch_size)} batch(es)")
    return vectors

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
