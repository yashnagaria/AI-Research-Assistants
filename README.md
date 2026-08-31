# Research Assistant with Multi-Agent Collaboration

A **Multi-Agent Research Assistant** built with **LangGraph, RAG, Persistent Memory, FAISS, and FastAPI**. It supports multi-format uploads, intelligent document analysis, and expert-like Q&A via Researcher, Summarizer, Critic, and Editor agents - offering deep, contextual, and interactive research insights.

This **Multi-Agent architecture** (Researcher, Summarizer, Critic, and Editor) simulates how real researchers process information. It integrates **FastAPI (backend), Next.js + TailwindCSS (frontend), FAISS (vector search), and SQLite** for conversation persistence.

---

## 🚀 Features

- 🧠 **Multi-Agent Workflow**
  - **Research Agent →** Finds relevant chunks using FAISS
  - **Summarizer Agent →** Creates concise summaries
  - **Critic Agent →** Identifies limitations and gaps
  - **Editor Agent →** Refines and formats final responses
- **📚 Multi-Document Support** → Upload and query multiple PDFs, DOCX, HTML, or TXT files
- **💬 Conversation Memory** → SQLite-backed memory for contextual, follow-up queries
- **🧩 Chunking & Embeddings** → Splits documents into chunks and embeds them via the configured provider
- **⚡ FAISS Vector Search** → High-speed semantic retrieval of embedded text chunks
- **🔄 LangGraph Orchestration** → Structured multi-agent pipeline with conditional routing
- **🎨 Modern UI** → Responsive frontend built with Next.js and TailwindCSS
- **🔌 Provider-Agnostic** → Runs on Google Gemini, OpenAI, or a local Ollama model by changing one `.env` variable

---

## 🏗️ Project Structure

```
AI-Research-Assistant/
├── backend/                           # FastAPI Backend
│   ├── agents/                        # Multi-Agent System
│   │   ├── __init__.py
│   │   ├── agent_state.py            # Shared state for LangGraph
│   │   ├── critic_agent.py           # Validates response quality
│   │   ├── editor_agent.py           # Refines final output
│   │   ├── langgraph_nodes.py        # LangGraph node definitions
│   │   ├── langgraph_workflow.py     # Workflow graph construction
│   │   ├── orchestrator.py           # Main workflow orchestrator
│   │   ├── research_agent.py         # Document retrieval agent
│   │   └── summarizer_agent.py       # Summarization agent
│   │
│   ├── db/                            # Database & Storage
│   │   ├── conversation_memory.py    # Legacy in-memory store (unused)
│   │   ├── conversations.db          # SQLite database (created at runtime)
│   │   ├── faiss_index.bin           # FAISS index for the legacy /upload route
│   │   ├── faiss_index_documents.pkl # Document metadata
│   │   ├── faiss_index_meta.pkl      # Chunk metadata
│   │   ├── faiss_store.py            # Single-index FAISS operations
│   │   ├── multi_doc_store.py        # Multi-document FAISS manager
│   │   ├── sqlite_memory.py          # SQLite conversation memory
│   │   └── documents/                # Per-document FAISS indexes
│   │       └── [doc_name]/
│   │           ├── index.bin
│   │           ├── metadata.pkl
│   │           └── info.pkl
│   │
│   ├── logs/                          # Application logs (created at runtime)
│   │   ├── agents.log
│   │   ├── api.log
│   │   ├── database.log
│   │   └── parser.log
│   │
│   ├── models/
│   │   └── schemas.py                # Pydantic request/response schemas
│   │
│   ├── utils/
│   │   ├── document_parser.py        # Multi-format document parser
│   │   ├── embeddings.py             # Embedding generation
│   │   ├── logger.py                 # Logging configuration
│   │   └── pdf_parser.py             # Legacy PDF parser (unused)
│   │
│   ├── config.py                      # Loads .env and exposes settings
│   ├── llm_client.py                  # Shared provider-agnostic API client
│   ├── main.py                        # FastAPI application & routes
│   └── requirements.txt               # Python dependencies
│
├── frontend/                          # Next.js Frontend
│   ├── components/
│   │   └── ChatBox.tsx               # Chat interface (the entire UI)
│   │
│   ├── pages/
│   │   ├── _app.tsx                  # App wrapper
│   │   └── index.tsx                 # Main page
│   │
│   ├── styles/
│   │   └── globals.css               # Global TailwindCSS styles
│   │
│   ├── next-env.d.ts
│   ├── package.json
│   ├── package-lock.json
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   └── tsconfig.json
│
├── venv/                              # Python virtual environment
│
├── .env                               # Environment variables (gitignored)
├── .env.example                       # Template for .env
├── .gitignore
└── README.md
```
---

## ⚙️ Tech Stack

### 🖥️ Backend
- **FastAPI**: High-performance async API framework
- **PDFPlumber**: PDF text extraction
- **Python-DOCX**: DOCX parsing
- **BeautifulSoup4 + lxml**: HTML parsing

### 🎨 Frontend
- **Next.js 15**: React framework (Pages Router)
- **TypeScript**: Type-safe development
- **TailwindCSS 4**: Utility-first styling
- **Axios**: HTTP client

### 🗄️ Databases
- **FAISS**: Vector similarity search (CPU)
- **SQLite**: Conversation memory persistence

### 🤖 AI
- **LangGraph**: Agent workflow orchestration
- **Google Gemini** (default): `gemini-3.5-flash-lite` for chat, `gemini-embedding-001` for embeddings

The backend talks to any **OpenAI-compatible** endpoint through `backend/llm_client.py`, so the provider is a configuration choice rather than a code change. See [Switching providers](#-switching-providers).

---

## 🔧 Prerequisites

- **Python 3.11** (standard CPython from [python.org](https://www.python.org/downloads/))
- **Node.js 18+**
- **A Google Gemini API key** - free from [Google AI Studio](https://aistudio.google.com/apikey), no billing required

> ⚠️ **Windows users:** if you have MSYS2, MinGW, or Cygwin installed, their `python` may shadow the real CPython on your `PATH`. Those builds cannot install `faiss-cpu` from PyPI, because PyPI's Windows wheels target CPython's MSVC ABI. Check which interpreters you have with `py -0p`, and use the `py -3.11` launcher (as shown below) rather than a bare `python` command.

---

## ⚡ Installation

### 1️⃣ Clone the repository

```bash
git clone https://github.com/yashnagaria/AI-Research-Assistant.git
cd AI-Research-Assistant
```

### 2️⃣ Environment configuration

Create a `.env` file in the **project root** (not inside `backend/`):

```env
OPENAI_API_KEY=your_gemini_api_key_here
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_MODEL=gemini-3.5-flash-lite
EMBEDDING_MODEL=gemini-embedding-001
VECTOR_DB_PATH=db/faiss_index
```

The variable is named `OPENAI_API_KEY` because the backend uses the `openai` Python SDK to speak to any OpenAI-compatible endpoint. With `OPENAI_BASE_URL` set, that key is your **Gemini** key and no request ever reaches OpenAI.

### 3️⃣ Backend setup

```bash
# Create and activate a virtual environment
py -3.11 -m venv venv          # Windows
python3.11 -m venv venv        # Linux/Mac

venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux/Mac

# Install dependencies
pip install -r backend/requirements.txt

# Run the server - note: from INSIDE the backend folder
cd backend
uvicorn main:app --reload --port 8000
```

> ⚠️ **Start the server from inside `backend/`.** All storage paths are relative to the working directory (`db/faiss_index.bin`, `db/documents/`, `db/conversations.db`, `logs/`). Launching from the project root scatters these into the wrong place.

> ⚠️ **Windows console encoding:** the logs contain emoji. If you see `UnicodeEncodeError` in your terminal, set `PYTHONUTF8=1` before starting:
> ```powershell
> $env:PYTHONUTF8 = "1"
> ```

### 4️⃣ Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Visit:

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs

---

## 🔌 Switching providers

Every API call flows through `get_client()` in `backend/llm_client.py`, which reads `OPENAI_BASE_URL`. Changing providers means editing `.env` only.

| Provider | `OPENAI_BASE_URL` | `LLM_MODEL` | `EMBEDDING_MODEL` |
|---|---|---|---|
| **Google Gemini** (free) | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-3.5-flash-lite` | `gemini-embedding-001` |
| **OpenAI** (paid) | *(leave blank or remove)* | `gpt-4o-mini` | `text-embedding-3-small` |
| **Ollama** (local, free) | `http://localhost:11434/v1` | `llama3.2` | `nomic-embed-text` |

> ⚠️ **Switching embedding models invalidates existing indexes.** A FAISS index is fixed to one vector dimension (Gemini's is 3072, OpenAI's `text-embedding-3-small` is 1536). After changing `EMBEDDING_MODEL`, delete `backend/db/documents/` and `backend/db/faiss_index*`, then re-upload your documents, or searches will fail on a dimension mismatch.

### On model choice

This app makes **three sequential LLM calls per question** (Summarizer → Critic → Editor). Reasoning models such as `gemini-3.6-flash` spend hidden "thinking" tokens on every call, measured here at roughly 7 seconds per call — about 2.5 minutes per question. `gemini-3.5-flash-lite` measured around 1.2 seconds for the same prompt. Prefer a lightweight, non-reasoning model unless you specifically need deeper analysis.

Model names are retired over time. To list the ones your key can currently reach:

```bash
curl -H "Authorization: Bearer $YOUR_KEY" \
  https://generativelanguage.googleapis.com/v1beta/openai/models
```

---

## 🧩 API Endpoints

### Document Management
- `POST /upload` - Upload document (legacy, single shared FAISS index)
- `POST /upload-v2` - Upload document (multi-doc, one index per file) — **used by the UI**
- `GET /documents` - List all uploaded documents

### Query Endpoints
- `POST /ask` - Simple RAG query, no agents (legacy)
- `POST /ask-agents` - Multi-agent workflow against the single FAISS index
- `POST /ask-v2` - Multi-document, multi-agent query with context switching — **used by the UI**

### Session Management
- `POST /sessions/create` - Create new conversation session
- `GET /sessions/{session_id}/history` - Get session history
- `DELETE /sessions/{session_id}` - Clear session
- `GET /sessions` - List all sessions

### Utilities
- `GET /health` - Health check
- `GET /workflow/diagram` - Get LangGraph workflow as a Mermaid diagram
- `GET /stats` - Database statistics

> The "Multi-Agent Mode" checkbox in the UI switches between `/ask-v2` (agents, multi-doc) and `/ask` (plain RAG, single index). Those two routes read **different** vector stores, so unchecking it finds nothing unless you have also uploaded through the legacy `/upload` route.

---

## 🧠 Multi-Agent Workflow

1. **Research Agent**: Searches documents using FAISS similarity search
2. **Summarizer Agent**: Condenses retrieved information
3. **Critic Agent**: Evaluates quality and completeness
4. **Editor Agent**: Produces final polished response

Agents communicate through a shared state managed by LangGraph. After the critic runs, the graph routes conditionally: if gaps were identified the Editor polishes the answer, otherwise the initial summary is used as-is.

---

## 🧾 Document Processing

Supported formats:
- **PDF**: Extracted using PDFPlumber
- **DOCX**: Parsed with python-docx
- **HTML**: Cleaned with BeautifulSoup4 (requires `lxml`)
- **TXT**: Direct text reading

Documents are:
1. Chunked into ~500 character segments with 50 characters of overlap
2. Embedded via the configured embedding model
3. Stored in FAISS vector indexes
4. Retrieved via semantic similarity search

> ⚠️ **Each chunk is a separate embedding API request.** A long PDF fires dozens of calls in quick succession and can hit free-tier rate limits. Start with small documents to confirm your setup before uploading large ones.

---

## 💬 Conversation Memory

- **Session-based**: Each conversation has a unique session ID
- **SQLite storage**: Persistent chat history in `backend/db/conversations.db`
- **Context retention**: The last 10 messages are passed to the Summarizer for follow-up queries
- **Metadata tracking**: Sources and workflow logs stored per message

---

## 🩺 Troubleshooting

| Symptom | Cause & fix |
|---|---|
| `ModuleNotFoundError: No module named 'langgraph'` | Virtual environment not activated, or dependencies not installed. |
| `faiss-cpu` fails to build on Windows | A non-CPython interpreter (MSYS2/MinGW) is first on `PATH`. Recreate the venv with `py -3.11 -m venv venv`. |
| `WARNING: OPENAI_API_KEY is not set` | `.env` is missing or misplaced. It belongs in the project root, one level **above** `backend/`. |
| `404 ... model is no longer available` | Model names change over time. List the current ones with the `curl` command above. |
| Answers take minutes | You are on a reasoning model. Set `LLM_MODEL=gemini-3.5-flash-lite`. |
| Dimension mismatch on query | `EMBEDDING_MODEL` changed after indexing. Delete `backend/db/documents/` and re-upload. |
| `UnicodeEncodeError` in the console on Windows | Set `PYTHONUTF8=1` before launching uvicorn. |
| Upload returns 400 "No text extracted" | The file is empty, image-only, or scanned. There is no OCR — the PDF must contain a real text layer. |
| Frontend cannot reach the backend | The API URL is hardcoded to `http://localhost:8000` in `frontend/components/ChatBox.tsx`. |

---

## 📜 Logging

Comprehensive logging across:
- API requests (`backend/logs/api.log`)
- Agent workflows (`backend/logs/agents.log`)
- Document parsing (`backend/logs/parser.log`)
- Database operations (`backend/logs/database.log`)

Console output is INFO level; the log files capture DEBUG and rotate at 10 MB.

---

## ⚠️ Known Limitations

- **CORS is fully open** (`allow_origins=["*"]` in `main.py`) — fine for local development, not for deployment.
- **No authentication** on any endpoint.
- **No document deletion route** is exposed, though `MultiDocumentStore.delete_document()` exists.
- **`tailwind.config.js` is inert.** It is written in Tailwind v3 format while the project uses Tailwind v4, which ignores it unless referenced via `@config`. Custom theme values there have no effect; edit `styles/globals.css` instead.
- **Legacy code retained:** `utils/pdf_parser.py` and `db/conversation_memory.py` are superseded by `utils/document_parser.py` and `db/sqlite_memory.py`.

---

## 🌟 Future Scope

- LangSmith integration for agent evaluation
- Audio/video research input (Whisper API)
- Multi-language summarization
- Graph visualization of the LangGraph workflow in the UI
- PDF/Word export for AI-generated reports
- Batched embedding requests to reduce rate-limit pressure

---

## 🪪 License

**MIT License** – Free to use and modify.

---
