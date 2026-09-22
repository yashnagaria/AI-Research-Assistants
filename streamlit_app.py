"""
Streamlit front end for the AI Research Assistant.

Runs the same LangGraph multi-agent pipeline as the FastAPI backend, but
in-process, so the whole app deploys to Streamlit Community Cloud straight
from GitHub with no separate API server.

    streamlit run streamlit_app.py
"""
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
EXAMPLES = ROOT / "examples"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
CONFIG_KEYS = ("OPENAI_API_KEY", "OPENAI_BASE_URL", "LLM_MODEL", "EMBEDDING_MODEL")

EXAMPLE_QUESTIONS = [
    "How many days a week can Brightline employees work remotely, and what are the core hours?",
    "What is the home-office equipment stipend?",
    "Does it renew every year?",
    "Summarize the architecture of the base Transformer model.",
    "What BLEU score did the big Transformer reach on English-to-German?",
    "What are the main failure modes of a RAG system?",
    "What is Brightline's policy on bringing pets to the office?",
]

st.set_page_config(page_title="AI Research Assistant", page_icon="🔎", layout="wide")


# ---------------------------------------------------------------------------
# Configuration: .env (local) -> Streamlit secrets (cloud) -> sidebar input
# ---------------------------------------------------------------------------
load_dotenv(ROOT / ".env")

try:
    for key in CONFIG_KEYS:
        if key in st.secrets and not os.environ.get(key):
            os.environ[key] = str(st.secrets[key])
except FileNotFoundError:  # no secrets.toml, e.g. running locally with .env
    pass

if not os.environ.get("OPENAI_API_KEY"):
    with st.sidebar:
        st.subheader("🔑 API key")
        pasted_key = st.text_input(
            "Google Gemini API key",
            type="password",
            help="Free from https://aistudio.google.com/apikey. Used only for this session.",
        )
    if not pasted_key:
        st.title("🔎 AI Research Assistant")
        st.info(
            "Paste a **Google Gemini API key** in the sidebar to start. "
            "Get one free at [Google AI Studio](https://aistudio.google.com/apikey).\n\n"
            "Deploying this app? Set `OPENAI_API_KEY` in the app's **Secrets** instead."
        )
        st.stop()
    os.environ["OPENAI_API_KEY"] = pasted_key
    os.environ.setdefault("OPENAI_BASE_URL", GEMINI_BASE_URL)

# Fast, non-reasoning defaults: the pipeline makes up to 3 LLM calls per question
os.environ.setdefault("LLM_MODEL", "gemini-3.5-flash-lite")
os.environ.setdefault("EMBEDDING_MODEL", "gemini-embedding-001")

# The backend resolves db/ and logs/ relative to backend/, and imports its
# packages (agents, db, utils) as top-level modules.
os.chdir(BACKEND)
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import faiss  # noqa: E402
import numpy as np  # noqa: E402

from agents.orchestrator import Orchestrator  # noqa: E402
from db.multi_doc_store import MultiDocumentStore  # noqa: E402
from utils.document_parser import SUPPORTED_EXTENSIONS, chunk_text, extract_text_from_file  # noqa: E402
from utils.embeddings import get_embeddings  # noqa: E402


@st.cache_resource
def get_orchestrator() -> Orchestrator:
    return Orchestrator()


# ---------------------------------------------------------------------------
# Per-session state: every visitor gets their own documents and chat
# ---------------------------------------------------------------------------
if "store" not in st.session_state:
    st.session_state.store = MultiDocumentStore(base_path=tempfile.mkdtemp(prefix="research_docs_"))
    st.session_state.messages = []

store: MultiDocumentStore = st.session_state.store


def index_document(filename: str, data: bytes) -> dict:
    """Parse, chunk, embed and index one file (mirrors POST /upload-v2)."""
    suffix = Path(filename).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(data)
    try:
        text, file_type = extract_text_from_file(tmp.name)
    finally:
        os.unlink(tmp.name)

    chunks = chunk_text(text)
    vectors = np.array(get_embeddings(chunks), dtype="float32")
    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(vectors)

    doc_info = {
        "original_filename": filename,
        "file_type": file_type,
        "upload_date": datetime.now().isoformat(),
        "characters": len(text),
        "chunks": len(chunks),
        "vectors": index.ntotal,
    }
    metadata = [{"chunk": c, "source": filename, "file_type": file_type} for c in chunks]
    store.save_document_index(doc_id=filename, index=index, metadata=metadata, doc_info=doc_info)
    return doc_info


def conversation_context(messages: list, max_messages: int = 10) -> str:
    """Same format as SQLiteConversationMemory.get_context()."""
    recent = messages[-max_messages:]
    if not recent:
        return ""
    lines = ["Previous conversation:"]
    lines += [f"{m['role'].capitalize()}: {m['content']}" for m in recent]
    return "\n".join(lines)


def render_trace(result: dict):
    """Show what each agent did for one answer."""
    meta = result.get("metadata", {})
    route = "✏️ Editor rewrote the draft" if meta.get("editing_applied") else "✅ Draft accepted, editor skipped"
    with st.expander(f"How the agents worked · {route}"):
        st.markdown("**Workflow log**")
        st.code("\n".join(result.get("workflow_log", [])), language=None)

        cols = st.columns(3)
        cols[0].metric("Chunks retrieved", meta.get("num_chunks", 0))
        cols[1].metric("Gaps found by critic", "Yes" if meta.get("has_gaps") else "No")
        cols[2].metric("Editor applied", "Yes" if meta.get("editing_applied") else "No")

        if result.get("critique"):
            st.markdown("**Critic's review of the first draft**")
            st.info(result["critique"])
        if meta.get("editing_applied") and result.get("initial_summary"):
            st.markdown("**First draft (before editing)**")
            st.caption(result["initial_summary"])

        sources = result.get("sources", [])
        if sources:
            st.markdown("**Sources:** " + ", ".join(sorted(set(sources))))


# ---------------------------------------------------------------------------
# Sidebar: documents
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("📚 Documents")

    uploads = st.file_uploader(
        "Upload PDF, DOCX, HTML or TXT",
        type=[ext.lstrip(".") for ext in SUPPORTED_EXTENSIONS],
        accept_multiple_files=True,
    )
    if uploads and st.button("Index uploaded files", type="primary", use_container_width=True):
        for f in uploads:
            with st.spinner(f"Indexing {f.name}..."):
                try:
                    info = index_document(f.name, f.getvalue())
                    st.success(f"{f.name}: {info['chunks']} chunks")
                except Exception as e:
                    st.error(f"{f.name}: {e}")

    if st.button("Load sample documents", use_container_width=True):
        for path in sorted(EXAMPLES.iterdir()):
            if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                with st.spinner(f"Indexing {path.name}..."):
                    try:
                        index_document(path.name, path.read_bytes())
                    except Exception as e:
                        st.error(f"{path.name}: {e}")

    docs = store.list_documents()
    if docs:
        names = {d["doc_id"]: d["original_filename"] for d in docs}
        selected = st.multiselect(
            "Search only these (empty = all)",
            options=list(names),
            format_func=names.get,
        )
        for d in docs:
            st.caption(f"📄 {d['original_filename']} · {d['file_type']} · {d['chunks']} chunks")
    else:
        selected = []
        st.caption("No documents yet. Upload your own or load the samples.")

    top_k = st.slider("Chunks to retrieve (top-k)", 2, 10, 5)

    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption(f"Model: `{os.environ['LLM_MODEL']}` · Embeddings: `{os.environ['EMBEDDING_MODEL']}`")


# ---------------------------------------------------------------------------
# Main: chat
# ---------------------------------------------------------------------------
st.title("🔎 AI Research Assistant")
st.caption(
    "Ask questions about your documents. Four agents (Research → Summarize → Critique → Edit) "
    "work together to write a grounded answer and check it for hallucinations."
)

with st.expander("How it works"):
    st.graphviz_chart(
        """
        digraph {
            rankdir=LR; node [shape=box, style=rounded];
            Q [label="Question\\n+ chat history"];
            R [label="Research Agent\\nFAISS top-k"];
            S [label="Summarizer\\ndraft answer"];
            C [label="Critic\\nfind gaps /\\nhallucinations"];
            E [label="Editor\\nrewrite"];
            A [label="Answer", shape=ellipse];
            Q -> R -> S -> C;
            C -> E [label="gaps"];
            C -> A [label="no gaps"];
            E -> A;
        }
        """
    )

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("result"):
            render_trace(msg["result"])

with st.expander("💡 Example questions (load the sample documents first)", expanded=not st.session_state.messages):
    cols = st.columns(2)
    for i, q in enumerate(EXAMPLE_QUESTIONS):
        if cols[i % 2].button(q, key=f"example_{i}", use_container_width=True):
            st.session_state.pending_question = q
            st.rerun()

question = st.chat_input("Ask about your documents...") or st.session_state.pop("pending_question", None)

if question:
    history = conversation_context(st.session_state.messages)
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        if not store.list_documents():
            answer, result = "Please upload a document or load the samples first (sidebar).", None
            st.warning(answer)
        else:
            with st.spinner("Agents are researching, drafting and reviewing..."):
                result = get_orchestrator().process_query_multi_doc(
                    query=question,
                    doc_ids=selected or None,
                    top_k=top_k,
                    conversation_context=history,
                    doc_store=store,
                )
            answer = result["answer"]
            if result["status"] == "error":
                st.error(answer)
                result = None
            else:
                st.markdown(answer)
                render_trace(result)

    st.session_state.messages.append({"role": "assistant", "content": answer, "result": result})
