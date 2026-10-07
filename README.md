# Local Agentic AI Research Assistant

A private, API-key-free research workspace that combines uploaded documents with live DuckDuckGo discovery. A LangGraph workflow coordinates Researcher, Summarizer, Critic, and Editor agents; Ollama runs generation and open-source embeddings locally, FAISS stores one index per document, and SQLite retains conversation history.

## Why it stands out

- **Three evidence modes:** private documents, current web results, or hybrid research.
- **Auditable web answers:** every result includes its title, URL, snippet, and retrieval time.
- **Self-correcting pipeline:** the critic checks grounding and citations before the editor produces the answer.
- **Local by design:** no provider account, API key, or document upload to a model vendor.
- **Per-document isolation:** select exactly which indexes participate in retrieval.
- **Visible agent trace:** the frontend exposes workflow stages for an interviewer demo.

See [ARCHITECTURE.md](ARCHITECTURE.md) for components, data flow, design decisions, and trade-offs.

## Prerequisites

- Python 3.11+
- Node.js 20+
- [Ollama](https://ollama.com/) installed locally

## Run locally

```powershell
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
ollama serve
```

In another terminal:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
Copy-Item .env.example .env
uvicorn main:app --app-dir backend --reload
```

In a third terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. After both Ollama models are pulled, document-only mode can run offline. Web and hybrid modes naturally require internet access.

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
- `POST /sessions/create`, `GET /sessions/{id}/history` — SQLite memory
- `GET /workflow/diagram` — Mermaid representation of the LangGraph

## Configuration

Copy `.env.example` to `.env`. There are no secrets. Good alternatives for `OLLAMA_CHAT_MODEL` include any chat model installed in Ollama. If you change the embedding model, delete locally generated indexes and re-upload documents because vector dimensions may differ.

## Privacy note

Document parsing, embeddings, vector search, conversations, and generation remain local. In Web or Hybrid mode, the search query is sent to DuckDuckGo; document contents are not sent.
