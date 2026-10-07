import { ChangeEvent, useEffect, useRef, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
type Mode = "documents" | "web" | "hybrid";
type Document = { doc_id: string; original_filename: string; chunks: number; file_type: string };
type WebSource = { title: string; url: string; snippet: string; retrieved_at: string };
type Message = { role: "user" | "assistant"; content: string; webSources?: WebSource[] };
type Session = { session_id: string; title: string; last_updated: string; message_count: number };

export default function ChatBox() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [sessionId, setSessionId] = useState<string>();
  const [mode, setMode] = useState<Mode>("documents");
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [workflow, setWorkflow] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("Checking local services...");
  const endRef = useRef<HTMLDivElement>(null);

  const loadDocuments = async () => {
    const response = await fetch(`${API}/documents`);
    if (!response.ok) return;
    const data = await response.json();
    const docs: Document[] = data.multi_docs || [];
    setDocuments(docs);
    setSelected((current) => current.length ? current : docs.map((doc) => doc.doc_id));
  };

  const loadSessions = async () => {
    const response = await fetch(`${API}/sessions?limit=5`);
    if (response.ok) setSessions((await response.json()).sessions || []);
  };

  useEffect(() => {
    Promise.all([fetch(`${API}/health`).then((response) => response.json()), loadDocuments(), loadSessions()])
      .then(([health]) => setStatus(health.ollama ? "Ollama online · local/private" : "Start Ollama to ask questions"))
      .catch(() => setStatus("Backend is offline"));
  }, []);
  useEffect(() => endRef.current?.scrollIntoView({ behavior: "smooth" }), [messages, busy]);

  const openSession = async (id: string) => {
    if (busy) return;
    const response = await fetch(`${API}/sessions/${id}/history`);
    if (!response.ok) return;
    const data = await response.json();
    setSessionId(id);
    setWorkflow([]);
    setMessages(data.messages.map((message: { role: "user" | "assistant"; content: string; metadata?: { web_sources?: WebSource[] } }) => ({
      role: message.role,
      content: message.content,
      webSources: message.metadata?.web_sources || [],
    })));
  };

  const newChat = () => { setSessionId(undefined); setMessages([]); setWorkflow([]); setQuery(""); };

  const upload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setBusy(true);
    const body = new FormData(); body.append("file", file);
    try {
      const response = await fetch(`${API}/upload-v2`, { method: "POST", body });
      if (!response.ok) throw new Error((await response.json()).detail || "Upload failed");
      setStatus(`${file.name} indexed locally`); await loadDocuments();
    } catch (error) { setStatus(error instanceof Error ? error.message : "Upload failed"); }
    finally { setBusy(false); event.target.value = ""; }
  };

  const send = async () => {
    if (!query.trim() || busy || (mode === "documents" && !selected.length)) return;
    const question = query.trim();
    setMessages((items) => [...items, { role: "user", content: question }]);
    setQuery(""); setBusy(true); setWorkflow([]);
    try {
      const response = await fetch(`${API}/ask-v2`, { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: question, doc_ids: selected, top_k: 5, session_id: sessionId, research_mode: mode }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Research failed");
      setSessionId(data.session_id); setWorkflow(data.workflow_log || []);
      setMessages((items) => [...items, { role: "assistant", content: data.answer, webSources: data.web_sources || [] }]);
      await loadSessions();
    } catch (error) {
      setMessages((items) => [...items, { role: "assistant", content: error instanceof Error ? error.message : "Research failed" }]);
    } finally { setBusy(false); }
  };

  return <main className="min-h-screen bg-[#070b14] text-slate-100">
    <div className="mx-auto max-w-[1500px] p-4 lg:p-7">
      <header className="mb-5 flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-800/80 bg-slate-900/60 px-5 py-4 shadow-2xl shadow-cyan-950/10 backdrop-blur">
        <div><p className="text-[11px] font-bold uppercase tracking-[.28em] text-cyan-400">Local Agentic RAG</p><h1 className="text-2xl font-semibold tracking-tight">Research Workbench</h1></div>
        <div className="flex items-center gap-3"><span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_12px_#34d399]"/><span className="text-xs text-slate-400">{status}</span><button onClick={newChat} className="rounded-xl bg-cyan-400 px-4 py-2 text-xs font-bold text-slate-950 hover:bg-cyan-300">+ New chat</button></div>
      </header>
      <div className="grid gap-4 xl:grid-cols-[260px_300px_1fr]">
        <aside className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
          <div className="mb-4 flex items-center justify-between"><h2 className="text-sm font-semibold">Recent chats</h2><span className="text-[10px] uppercase tracking-wider text-slate-500">Last 5</span></div>
          <div className="space-y-2">{sessions.length === 0 && <p className="rounded-xl border border-dashed border-slate-700 p-4 text-xs leading-5 text-slate-500">Your recent conversations will appear here and remain available after restart.</p>}{sessions.map((session) =>
            <button key={session.session_id} onClick={() => openSession(session.session_id)} className={`w-full rounded-xl border p-3 text-left transition ${sessionId === session.session_id ? "border-cyan-400/70 bg-cyan-400/10" : "border-slate-800 bg-slate-950/60 hover:border-slate-600"}`}>
              <span className="block truncate text-xs font-medium text-slate-200">{session.title}</span><span className="mt-1 block text-[10px] text-slate-500">{session.message_count} messages · {new Date(session.last_updated).toLocaleDateString()}</span>
            </button>)}</div>
          {workflow.length > 0 && <div className="mt-6 border-t border-slate-800 pt-4"><p className="mb-3 text-xs font-bold uppercase tracking-wider text-cyan-400">Agent trace</p>{workflow.map((step, index) => <div key={`${step}-${index}`} className="mb-2 flex gap-2 text-[11px] leading-4 text-slate-400"><span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-cyan-400"/>{step}</div>)}</div>}
        </aside>
        <aside className="space-y-5 rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
          <div><label className="mb-2 block text-sm font-semibold">Evidence source</label><div className="grid grid-cols-3 gap-1 rounded-xl bg-slate-950 p-1">{(["documents", "web", "hybrid"] as Mode[]).map((item) => <button key={item} onClick={() => setMode(item)} className={`rounded-lg px-2 py-2 text-[11px] capitalize transition ${mode === item ? "bg-cyan-400 font-bold text-slate-950" : "text-slate-400 hover:text-white"}`}>{item}</button>)}</div><p className="mt-2 text-[11px] leading-4 text-slate-500">{mode === "documents" ? "Private, offline document retrieval." : mode === "web" ? "Current web research with citations." : "Compare local knowledge with live evidence."}</p></div>
          <label className="block cursor-pointer rounded-xl border border-dashed border-slate-600 p-4 text-center text-xs text-slate-300 transition hover:border-cyan-400 hover:bg-cyan-400/5">{busy ? "Working..." : "Upload PDF, DOCX, HTML or TXT"}<input type="file" className="hidden" accept=".pdf,.docx,.html,.htm,.txt" onChange={upload} disabled={busy}/></label>
          <div><div className="mb-2 flex justify-between text-sm font-semibold"><span>Document scope</span><button className="text-[11px] text-cyan-400" onClick={() => setSelected(selected.length === documents.length ? [] : documents.map((doc) => doc.doc_id))}>Toggle all</button></div><div className="max-h-[42vh] space-y-2 overflow-auto pr-1">{documents.map((doc) => <label key={doc.doc_id} className="flex cursor-pointer gap-2 rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-xs hover:border-slate-600"><input type="checkbox" checked={selected.includes(doc.doc_id)} onChange={() => setSelected((ids) => ids.includes(doc.doc_id) ? ids.filter((id) => id !== doc.doc_id) : [...ids, doc.doc_id])}/><span className="min-w-0 truncate">{doc.original_filename}<small className="mt-1 block text-slate-500">{doc.chunks} chunks · {doc.file_type}</small></span></label>)}</div></div>
        </aside>
        <section className="flex min-h-[76vh] flex-col overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70">
          <div className="flex-1 space-y-5 overflow-auto p-5 lg:p-7">{messages.length === 0 && <div className="grid h-full place-content-center text-center"><div className="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-2xl border border-cyan-400/20 bg-cyan-400/10 text-2xl">⌁</div><p className="text-lg font-medium text-slate-200">Build an evidence-backed answer</p><p className="mt-1 max-w-sm text-sm text-slate-500">Choose a source mode, select your documents, and ask a focused research question.</p></div>}{messages.map((message, index) => <article key={index} className={`max-w-3xl rounded-2xl px-4 py-3 ${message.role === "user" ? "ml-auto bg-cyan-400 text-slate-950" : "border border-slate-700/70 bg-slate-800/80"}`}><p className="whitespace-pre-wrap text-sm leading-6">{message.content}</p>{!!message.webSources?.length && <div className="mt-4 border-t border-slate-700 pt-3"><p className="mb-2 text-[10px] font-bold uppercase tracking-widest text-cyan-400">Web evidence</p>{message.webSources.map((source, sourceIndex) => <a key={source.url} href={source.url} target="_blank" rel="noreferrer" className="mb-2 block truncate text-xs text-cyan-300 hover:underline">[{sourceIndex + 1}] {source.title}</a>)}</div>}</article>)}{busy && <div className="flex items-center gap-3 text-sm text-cyan-300"><span className="h-2 w-2 animate-pulse rounded-full bg-cyan-400"/>Agents are researching, critiquing, and editing...</div>}<div ref={endRef}/></div>
          <div className="border-t border-slate-800 bg-slate-950/40 p-4"><div className="flex gap-3"><textarea aria-label="Research question" rows={2} className="flex-1 resize-none rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-cyan-400" value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); send(); } }} placeholder="Ask about your documents or a current topic..."/><button onClick={send} disabled={busy || !query.trim()} className="rounded-xl bg-cyan-400 px-6 text-sm font-bold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-40">Research</button></div><p className="mt-2 text-[10px] text-slate-600">Enter to send · Shift + Enter for a new line · history is stored locally in SQLite</p></div>
        </section>
      </div>
    </div>
  </main>;
}
