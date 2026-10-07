# Local Agentic AI Research Assistant

A private, API-key-free research workspace that combines uploaded documents with live DuckDuckGo discovery. A LangGraph workflow coordinates Researcher, Summarizer, Critic, and Editor agents; Ollama runs generation and open-source embeddings locally, FAISS stores one index per document, and SQLite retains conversation history.

## Why it stands out

- **Three evidence modes:** private documents, current web results, or hybrid research.
- **Auditable web answers:** every result includes its title, URL, snippet, and retrieval time.
- **Self-correcting pipeline:** the critic checks grounding and citations before the editor produces the answer.
- **Local by design:** no provider account, API key, or document upload to a model vendor.
- **Per-document isolation:** select exactly which indexes participate in retrieval.
- **Visible agent trace:** the frontend exposes workflow stages for an interviewer demo.
- **Persistent recent chats:** SQLite stores every turn and the UI can reopen the latest five conversations after a restart.

See [ARCHITECTURE.md](ARCHITECTURE.md) for components, data flow, design decisions, and trade-offs.

## Prerequisites

- Python 3.11+
- Node.js 20+
- [Ollama](https://ollama.com/) installed locally

## First-time setup

```powershell
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
ollama serve
```

From the project root, prepare the backend:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
Copy-Item .env.example .env
```

Prepare the frontend:

```powershell
cd frontend
npm install
```

## Run the application

Use three PowerShell terminals. If the Ollama desktop application is already running, skip `ollama serve`; the port `11434` message simply means Ollama is already available.

Terminal 1 — Ollama:

```powershell
ollama serve
```

Terminal 2 — FastAPI, from the project root:

```powershell
.\venv\Scripts\Activate.ps1
uvicorn main:app --app-dir backend --reload
```

Terminal 3 — Next.js:

```powershell
cd frontend
npm run dev
```

Open `http://localhost:3000`. After both Ollama models are pulled, document-only mode can run offline. Web and hybrid modes naturally require internet access.

Useful checks:

```powershell
ollama list
Invoke-RestMethod http://localhost:11434/api/tags
Invoke-RestMethod http://localhost:8000/health
```

If PowerShell blocks virtual-environment activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

## Conversation history

Each user and assistant message is written to local SQLite storage. The left sidebar shows the five most recently updated conversations; selecting one restores its messages and web citations. **New chat** starts a separate session. History never leaves the machine and generated database files are excluded from Git.

## Demo flow

1. Upload two documents and ask a comparative question in **Documents** mode.
2. Switch to **Web** and research a recent topic; open the returned citations.
3. Use **Hybrid** to compare internal evidence with current public information.
4. Point out the visible Research → Summarize → Critique → Edit trace.

## API

- `GET /health` — backend and Ollama readiness (also confirms no API key is required)
- `POST /upload-v2` — parse and create an isolated FAISS index
- `POST /ask-v2` — run `documents`, `web`, or `hybrid` agent research
- `GET /documents` — list indexed documents
- `GET /sessions?limit=5` — recent sessions with titles and timestamps
- `POST /sessions/create`, `GET /sessions/{id}/history` — SQLite conversation memory
- `GET /workflow/diagram` — Mermaid representation of the LangGraph

## Configuration

Copy `.env.example` to `.env`. There are no secrets. Good alternatives for `OLLAMA_CHAT_MODEL` include any chat model installed in Ollama. If you change the embedding model, delete locally generated indexes and re-upload documents because vector dimensions may differ.

## Privacy note

Document parsing, embeddings, vector search, conversations, and generation remain local. In Web or Hybrid mode, the search query is sent to DuckDuckGo; document contents are not sent.
