import { ChangeEvent, useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
type Mode = "documents" | "web" | "hybrid";
type Document = { doc_id: string; original_filename: string; chunks: number; file_type: string };
type WebSource = { title: string; url: string; snippet: string; retrieved_at: string };
type Message = { role: "user" | "assistant"; content: string; webSources?: WebSource[] };

export default function ChatBox() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [mode, setMode] = useState<Mode>("documents");
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [workflow, setWorkflow] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("Checking local services...");
  const [sessionId, setSessionId] = useState<string>();

  const loadDocuments = async () => {
    const response = await fetch(`${API}/documents`);
    if (!response.ok) return;
    const data = await response.json();
    setDocuments(data.multi_docs || []);
    setSelected((current) => current.length ? current : (data.multi_docs || []).map((d: Document) => d.doc_id));
  };

  useEffect(() => {
    Promise.all([fetch(`${API}/health`).then((r) => r.json()), loadDocuments()])
      .then(([health]) => setStatus(health.ollama ? "Ollama online · local/private" : "Start Ollama to ask questions"))
      .catch(() => setStatus("Backend is offline"));
  }, []);

  const upload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setBusy(true);
    const body = new FormData();
    body.append("file", file);
    try {
      const response = await fetch(`${API}/upload-v2`, { method: "POST", body });
      if (!response.ok) throw new Error((await response.json()).detail || "Upload failed");
      setStatus(`${file.name} indexed locally`);
      await loadDocuments();
    } catch (error) { setStatus(error instanceof Error ? error.message : "Upload failed"); }
    finally { setBusy(false); event.target.value = ""; }
  };

  const send = async () => {
    if (!query.trim() || busy || (mode === "documents" && !selected.length)) return;
    const question = query.trim();
    setMessages((items) => [...items, { role: "user", content: question }]);
    setQuery(""); setBusy(true); setWorkflow([]);
    try {
      const response = await fetch(`${API}/ask-v2`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: question, doc_ids: selected, top_k: 5,
          session_id: sessionId, research_mode: mode }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Research failed");
      setSessionId(data.session_id); setWorkflow(data.workflow_log || []);
      setMessages((items) => [...items, { role: "assistant", content: data.answer,
        webSources: data.web_sources || [] }]);
    } catch (error) {
      setMessages((items) => [...items, { role: "assistant",
        content: error instanceof Error ? error.message : "Research failed" }]);
    } finally { setBusy(false); }
  };

  return <main className="min-h-screen bg-slate-950 text-slate-100">
    <div className="mx-auto max-w-7xl p-5 lg:p-8">
      <header className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div><p className="text-xs font-semibold uppercase tracking-[.25em] text-cyan-400">Local Agentic RAG</p>
          <h1 className="text-3xl font-bold">Research Workbench</h1>
          <p className="mt-1 text-sm text-slate-400">Private documents + live web evidence · no API keys</p></div>
        <span className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-300">{status}</span>
      </header>
      <div className="grid gap-5 lg:grid-cols-[320px_1fr]">
        <aside className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900 p-4">
          <div><label className="mb-2 block text-sm font-semibold">Research mode</label>
            <div className="grid grid-cols-3 gap-1 rounded-xl bg-slate-950 p-1">
              {(["documents", "web", "hybrid"] as Mode[]).map((item) =>
                <button key={item} onClick={() => setMode(item)} className={`rounded-lg px-2 py-2 text-xs capitalize ${mode === item ? "bg-cyan-500 font-bold text-slate-950" : "text-slate-400"}`}>{item}</button>)}
            </div></div>
          <label className="block cursor-pointer rounded-xl border border-dashed border-slate-600 p-4 text-center text-sm hover:border-cyan-400">
            {busy ? "Working..." : "Upload PDF, DOCX, HTML or TXT"}<input type="file" className="hidden" accept=".pdf,.docx,.html,.htm,.txt" onChange={upload} disabled={busy}/>
          </label>
          <div><div className="mb-2 flex justify-between text-sm font-semibold"><span>Document scope</span><button className="text-xs text-cyan-400" onClick={() => setSelected(selected.length === documents.length ? [] : documents.map((d) => d.doc_id))}>toggle all</button></div>
            <div className="max-h-60 space-y-2 overflow-auto">{documents.map((doc) =>
              <label key={doc.doc_id} className="flex gap-2 rounded-lg bg-slate-950 p-3 text-xs"><input type="checkbox" checked={selected.includes(doc.doc_id)} onChange={() => setSelected((ids) => ids.includes(doc.doc_id) ? ids.filter((id) => id !== doc.doc_id) : [...ids, doc.doc_id])}/><span className="truncate">{doc.original_filename}<small className="block text-slate-500">{doc.chunks} chunks · {doc.file_type}</small></span></label>)}</div>
          </div>
          {workflow.length > 0 && <div><p className="mb-2 text-sm font-semibold">Agent trace</p>{workflow.map((step) => <p key={step} className="mb-1 text-xs text-slate-400">{step}</p>)}</div>}
        </aside>
        <section className="flex min-h-[70vh] flex-col rounded-2xl border border-slate-800 bg-slate-900">
          <div className="flex-1 space-y-5 overflow-auto p-5">{messages.length === 0 && <div className="grid h-full place-content-center text-center text-slate-500"><p className="text-lg text-slate-300">Ask a research question</p><p className="text-sm">Choose documents, live web, or combine both.</p></div>}
            {messages.map((message, index) => <article key={index} className={`max-w-3xl rounded-2xl p-4 ${message.role === "user" ? "ml-auto bg-cyan-500 text-slate-950" : "bg-slate-800"}`}>
              <p className="whitespace-pre-wrap text-sm leading-6">{message.content}</p>
              {!!message.webSources?.length && <div className="mt-4 border-t border-slate-700 pt-3"><p className="mb-2 text-xs font-bold uppercase tracking-wide text-cyan-400">Web evidence</p>{message.webSources.map((source, i) => <a key={source.url} href={source.url} target="_blank" rel="noreferrer" className="mb-2 block text-xs text-cyan-300 hover:underline">[{i + 1}] {source.title}</a>)}</div>}
            </article>)}{busy && <p className="text-sm text-cyan-400">Agents are researching, critiquing, and editing...</p>}</div>
          <div className="flex gap-3 border-t border-slate-800 p-4"><input aria-label="Research question" className="flex-1 rounded-xl bg-slate-950 px-4 py-3 outline-none ring-cyan-400 focus:ring-2" value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()} placeholder="Ask about your documents or a current topic..."/><button onClick={send} disabled={busy || !query.trim()} className="rounded-xl bg-cyan-500 px-5 font-bold text-slate-950 disabled:opacity-40">Research</button></div>
        </section>
      </div>
    </div>
  </main>;
}
