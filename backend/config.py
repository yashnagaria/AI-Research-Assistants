"""Local-only application configuration. No cloud API key is required."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "180"))
LLM_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "qwen2.5:3b")
EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "db/faiss_index")
WEB_RESULTS_LIMIT = int(os.getenv("WEB_RESULTS_LIMIT", "5"))
