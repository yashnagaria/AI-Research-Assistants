"""
Configuration loader.

Importing this module is what loads the .env file for the whole backend,
so it must be imported before anything reads an environment variable.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# .env lives at the project root, one level above this backend/ folder
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.6-flash")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "db/faiss_index")

if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY is not set - check your .env at the project root")
