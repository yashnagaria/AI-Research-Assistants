# AI Research Assistant: Interview Guide

How to present this project in an interview: the pitch, the build story, the design decisions, and answers to the questions you are likely to get.

---

## 1. The 30-second pitch

> "I built a multi-agent research assistant that answers questions about your own documents: PDFs, Word files, web pages. Most document chatbots are a single retrieve-then-answer step, and they hallucinate. I split the work across four agents, the way a research team would. A **Researcher** finds the relevant passages with FAISS vector search. A **Summarizer** drafts an answer strictly from those passages. A **Critic** checks the draft for hallucinations and missing facts. An **Editor** rewrites the answer, but only when the Critic actually found a problem. LangGraph orchestrates the pipeline with conditional routing, SQLite gives it conversation memory for follow-up questions, and it is provider-agnostic: it runs on free Google Gemini, OpenAI, or a local Ollama model by changing one config line. It has a FastAPI + Next.js version and a Streamlit version deployed from GitHub."

## 2. What problem it solves (use cases)

The core use case: **"I have a pile of documents and need trustworthy answers from them, fast, with sources."**

| Who | Example |
|---|---|
| **Students & researchers** | Upload 5 papers, ask "What datasets did these papers evaluate on?" or "Summarize the architecture in paper X". |
| **Employees / HR** | Upload the company handbook: "How many remote days do I get?", "Does the equipment stipend renew?" |
| **Legal / compliance** | Query contracts and policies. The grounding rules matter most here, because a made-up clause is worse than "not found". |
| **Analysts & consultants** | Load several client reports and restrict a question to specific documents with the document selector. |
| **Support teams** | Answer from product manuals and FAQs instead of general web knowledge. |

**Why not just paste the document into ChatGPT?** Documents often exceed the context window. You want answers **only** from your sources, not from the model's general knowledge. You want citations. You want follow-up questions to work across a session. And you may need to run it on a local model (Ollama) for private data.

---

## 3. The build story

Tell it as a series of problems and the decision each one forced. Interviewers remember a story better than a feature list.

### Chapter 1: Start simple: plain RAG
I started with the textbook RAG pipeline: parse a PDF, split it into ~500-character chunks with 50 characters of overlap, embed each chunk, store the vectors in a FAISS index, and at query time retrieve the top-5 chunks and ask the LLM to answer. This is the `/upload` + `/ask` route, and it still exists as the baseline.

**Problem:** the answers *sounded* right but mixed in facts from the model's general knowledge. For a research tool that is the worst failure mode, because the user cannot tell which sentence came from the document.

### Chapter 2: Split the job into agents
Instead of one prompt doing everything, I modelled how a careful human researcher works:

1. **Research Agent**: retrieves evidence (no LLM, just vector search)
2. **Summarizer Agent**: drafts an answer with strict grounding rules and low temperature (0.2)
3. **Critic Agent**: compares the draft to the source chunks and lists *strengths / gaps / suggestions*, including hallucinations
4. **Editor Agent**: rewrites the draft using the critique, removing unsupported claims and adding missed facts

Separating "write" from "review" works because a model is better at *checking* an answer against evidence than at producing a perfect one in a single pass.

### Chapter 3: Orchestrate with LangGraph and routing that saves cost
My first orchestrator was plain sequential Python. I moved it to **LangGraph**, where each agent is a node that reads and writes a shared typed state (`AgentState`). The main win is **conditional edges**: after the Critic runs, a router function (`should_edit`) sends the answer to the Editor **only if gaps were found**, and otherwise ends the run.

That cuts a question from 3 LLM calls to 2 whenever the first draft is already good. It also gives me a graph I can visualize (the `/workflow/diagram` endpoint exports Mermaid).

**A bug I found and fixed:** the Critic's gap check originally tested whether the text after `GAPS:` was longer than 10 characters. A clean review reads `GAPS: None. SUGGESTIONS: None.`, and even that is longer than 10 characters, so the Editor ran almost every time and the routing was effectively dead. I changed it to parse only the GAPS section and treat "None" as no gaps. *(Good example of "parsing free-text LLM output is fragile". The robust fix is structured JSON output; see section 7.)*

### Chapter 4: Multiple documents without cross-contamination
With several documents in one shared index, users couldn't say "only search the contract". I built a **multi-document store** (`MultiDocumentStore`): one FAISS index per document, plus metadata and info files. At query time the Research Agent searches only the selected indexes and merges the results by distance.

Merging raw L2 distances across separate indexes is valid because every index uses the same embedding model and the same vector space. That is also why switching embedding models means re-indexing everything: the vector dimension changes (Gemini 3072 vs OpenAI `text-embedding-3-small` 1536).

### Chapter 5: Memory for follow-up questions
"Does it renew every year?" means nothing without the previous turn. I added **SQLite-backed conversation memory** with sessions and messages tables. The last 10 messages are formatted into the Summarizer's prompt, so it can resolve "it", "that one" and "what about…". I chose SQLite because it has zero setup, persists across restarts, and is plenty for single-server scale.

### Chapter 6: Provider-agnostic and free to run
I didn't want the project locked to a paid API. Every call goes through one `get_client()` factory using the OpenAI SDK against any **OpenAI-compatible** endpoint. Google Gemini (free tier), OpenAI, and local Ollama each need only a `.env` change, with no code change.

### Chapter 7: Performance tuning, with real numbers
- **Model choice:** a reasoning model (`gemini-3.6-flash`) spent hidden "thinking" tokens on every call: about **7 s per call, roughly 2.5 minutes per question**. A lightweight model (`gemini-3.5-flash-lite`) took about **1.2 s per call**. For an extract-and-verify pipeline, a fast non-reasoning model is the right trade-off.
- **Embedding batching:** indexing made one API request per chunk, so a long PDF fired dozens of requests and hit free-tier rate limits. I batched them (up to 100 texts per request) with a fallback to per-chunk calls for providers that reject list input.

### Chapter 8: Ship it: Streamlit + GitHub deploy
The full stack (FastAPI + Next.js) needs two servers, which is a barrier for a demo. I added `streamlit_app.py`, which imports the **same agents and LangGraph workflow in-process**, so the whole thing deploys to Streamlit Community Cloud from the GitHub repo with one click.

Two deployment details I had to design for:
- **Per-session isolation:** a public app must not show one visitor's uploads to another, so each browser session gets its own temporary `MultiDocumentStore` instance, passed through the LangGraph state.
- **Secrets:** the API key comes from Streamlit Secrets. If the app has none, each visitor can paste their own key.

The UI also exposes the agents' reasoning. For every answer you can open **How the agents worked** to see the workflow log, the Critic's review, whether the Editor ran, the first draft before editing, and the sources.

---

## 4. Architecture at a glance

```
                ┌──────────── Indexing ────────────┐
 PDF/DOCX/HTML/TXT → parse → chunk (500/50) → embed (batched) → FAISS index per document

                ┌──────────── Answering (LangGraph) ────────────┐
 Question + last 10 messages
        │
        ▼
 [Research Agent] ── FAISS top-k over selected docs
        │
        ▼
 [Summarizer] ── grounded draft (temp 0.2)
        │
        ▼
 [Critic] ── STRENGTHS / GAPS / SUGGESTIONS (temp 0.4)
        │
   gaps? ──yes──▶ [Editor] ── rewrite from context (temp 0.3) ──▶ Answer + sources
        │
        no ─────────────────────────────────────────────────────▶ Answer + sources
```

**Tech stack:** Python, LangGraph, FAISS, OpenAI SDK (OpenAI-compatible providers: Gemini / OpenAI / Ollama), FastAPI, SQLite, Next.js + TypeScript + Tailwind, Streamlit, pdfplumber, python-docx, BeautifulSoup.

**Numbers worth remembering:** 4 agents · 2–3 LLM calls per question · chunks of 500 chars with 50 overlap · top-k = 5 · last 10 messages of memory · 4 file formats · ~1.2 s vs ~7 s per LLM call (lite vs reasoning model).

---

## 5. Key design decisions and trade-offs

| Decision | Why | Trade-off |
|---|---|---|
| Multi-agent write → critique → edit | Self-review catches hallucinations a single prompt misses | More latency and tokens, reduced by conditional routing |
| LangGraph over hand-written chaining | Typed shared state, conditional edges, visualizable graph, easy to add nodes | Extra dependency and some learning curve |
| FAISS `IndexFlatL2` (exact search) | Exact and simple, fast enough for thousands of chunks | Slows down at millions of vectors; would switch to IVF/HNSW |
| One index per document | Clean document filtering and easy deletion | Querying many docs means loading many indexes |
| Character chunking (500/50) | Simple, predictable, format-agnostic | Can split mid-sentence; semantic or token-based chunking would be better |
| SQLite memory | Zero setup and persistent | Single-writer; would use Postgres or Redis at scale |
| OpenAI-compatible client | Switch providers by config; free Gemini tier for demos | Limited to features the compatibility layer supports |
| Streamlit in-process app | One-click deploy, no second server | Not suited to high concurrency; the FastAPI version is the scalable path |

---

## 6. Demo script (about 3 minutes)

1. Open the Streamlit app and click **Load sample documents**: a RAG primer, Transformer paper notes (HTML) and a fictional company remote-work policy.
2. **Precise fact:** *"How many days a week can Brightline employees work remotely, and what are the core hours?"* → "3 days; 10:00–15:00". Open **How the agents worked** and show that the Critic found no gaps, so the Editor was skipped.
3. **Memory:** *"What is the home-office equipment stipend?"* then *"Does it renew every year?"* → "No, it's one-time; a second 300 USD stipend is possible after 3 years." The second question only works because of conversation memory.
4. **Complex answer:** *"Summarize the architecture of the base Transformer model."* → show the Critic's review and, if the Editor ran, the first draft next to the final answer.
5. **Hallucination guard (the strongest moment):** *"What is Brightline's policy on bringing pets to the office?"* → the assistant says it is not in the document instead of inventing a plausible policy.
6. **Document scoping:** select only `transformer_notes.html` and ask *"What BLEU score did the big Transformer reach on English-to-German?"* → 28.4.

---

## 7. Honest limitations and what I'd do next

Interviewers respect a candidate who knows the weak spots of their own system.

- **Free-text parsing of the Critic's output is fragile.** Next step: structured output (JSON schema) with an explicit `has_gaps: bool` and a list of unsupported claims.
- **No retrieval evaluation yet.** I'd build a small labelled question set and measure faithfulness, answer relevance, and context precision/recall (e.g., with RAGAS or LangSmith).
- **Chunking is character-based.** I'd try sentence- or token-aware chunking and hybrid search (BM25 + vectors) with a re-ranker, which helps when the question's wording differs from the document's.
- **No OCR:** scanned PDFs yield no text.
- **Security for production:** CORS is open and there is no authentication on the FastAPI routes. The Streamlit version isolates sessions, but storage is ephemeral.
- **Latency:** the agents run sequentially. Streaming the final answer and caching embeddings for repeated documents would improve the experience.
- **Citations are per-document, not per-sentence.** Inline citations pointing to the exact chunk would make answers easier to verify.

---

## 8. Likely interview questions and strong answers

**Q: Why multiple agents instead of one good prompt?**
One prompt has to retrieve, reason, write and self-check at once, and in practice it skips the self-check. Separating the roles gives each call one job with focused instructions and a different temperature. The Critic sees the draft *and* the source chunks, so it can catch claims that are not supported. Conditional routing keeps the extra cost to one call, and only when it is needed.

**Q: How do you reduce hallucinations?**
Three layers. (1) Grounding rules in the Summarizer prompt: answer only from context, otherwise say "not found", at temperature 0.2. (2) A Critic pass that explicitly checks for information not present in the context. (3) An Editor that removes flagged claims using the context as "the only source of truth". Showing sources lets the user verify.

**Q: What is RAG and why use it instead of fine-tuning?**
RAG retrieves relevant passages at query time and puts them in the prompt. It is cheaper than fine-tuning, updates instantly when documents change, works with private data, and supports citations. Fine-tuning teaches style or behaviour, not reliably new facts.

**Q: How does FAISS work here? Why L2?**
Each chunk becomes a dense vector. `IndexFlatL2` computes exact Euclidean distance between the query vector and every stored vector and returns the k nearest. For normalized embeddings, L2 and cosine similarity produce the same ranking. At larger scale I'd use an approximate index such as IVF or HNSW.

**Q: Why LangGraph?**
It models the workflow as a state machine: nodes are agents, edges are transitions, and conditional edges route on the state. The typed shared state makes every agent's inputs and outputs explicit, and it's easy to extend with a retry loop (Critic → Editor → Critic) or a web-search node.

**Q: How would you scale this to 10,000 users?**
Run the FastAPI backend statelessly behind a load balancer. Move vectors into a managed vector DB (pgvector, Qdrant, Pinecone) with per-tenant namespaces, and memory into Postgres or Redis. Do embedding as background jobs on a queue. Stream responses. Cache embeddings by content hash. Add authentication and rate limiting.

**Q: What was the hardest bug?**
Pick one:
- **The routing bug:** the Critic's "has gaps" check was always true, so the Editor always ran and the conditional routing never did anything. I found it by reading the workflow logs, which never showed a skipped Editor.
- **Latency:** answers took minutes because the default was a reasoning model. Measuring per-call latency (~7 s vs ~1.2 s) led me to a lightweight model.
- **Windows setup:** `faiss-cpu` failed to install because an MSYS2 Python was shadowing CPython on the PATH. PyPI's Windows wheels target CPython's MSVC ABI.

**Q: How do follow-up questions work?**
Each session stores messages in SQLite (in `st.session_state` for the Streamlit app). The last 10 are formatted as "User: … / Assistant: …" and prepended to the Summarizer's prompt, which is told to use them to resolve references such as "it" or "that one".

**Q: What if the answer spans two documents?**
With no documents selected, the Research Agent searches every document's index, merges the candidates by distance and keeps the global top-k. The Summarizer then sees chunks from both documents.

**Q: How would you evaluate it?**
Build a golden set of question, expected-answer and source triples. Measure retrieval with recall@k (is the right chunk retrieved?) and generation with faithfulness and relevance, using an LLM judge plus spot checks. Also track the rate at which the Critic flags gaps and the Editor runs, which is a cheap proxy for draft quality.

---

## 9. Résumé bullet points

- Built a **multi-agent RAG research assistant** (Researcher, Summarizer, Critic, Editor) orchestrated with **LangGraph** conditional routing, cutting LLM calls per query from 3 to 2 when the first draft passes review.
- Implemented **per-document FAISS vector indexes** with cross-document retrieval and document scoping over **PDF, DOCX, HTML and TXT** sources.
- Added **SQLite conversation memory** for context-aware follow-up questions and a **provider-agnostic LLM layer** (Gemini / OpenAI / Ollama) switchable by configuration.
- Cut per-call latency from **~7 s to ~1.2 s** by moving from a reasoning model to a lightweight model, and **batched embedding requests** to stay within free-tier rate limits.
- Shipped a **FastAPI + Next.js** full-stack version and a **Streamlit** version deployed from GitHub with per-session data isolation.
