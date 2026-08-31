"""
Shared OpenAI-compatible client.

The project talks to whichever provider OPENAI_BASE_URL points at
(OpenAI, Google Gemini, Ollama, ...). Importing config first guarantees
the .env file is loaded before we read any environment variables.
"""
import os

import config  # noqa: F401  -- imported for its side effect: loads .env

from openai import OpenAI


def get_client() -> OpenAI:
    """Build a client pointed at the configured provider."""
    return OpenAI(
        api_key=os.getenv("OPENAI_API_KEY", "not-needed"),
        base_url=os.getenv("OPENAI_BASE_URL") or None,
    )