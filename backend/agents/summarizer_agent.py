"""Grounded answer drafting agent."""
from llm_client import ollama_client
from utils.logger import agent_logger


class SummarizerAgent:
    name = "Summarizer Agent"

    def summarize(self, query: str, chunks: list[str], conversation_context: str = ""):
        if not chunks:
            return {"status": "error", "message": "No evidence was retrieved", "summary": ""}
        evidence = "\n\n---\n\n".join(chunks)
        prompt = f"""Answer the question only from the supplied evidence. Cite evidence markers
such as [1] when present. If evidence is insufficient, say so. Never invent a source.

Conversation context:
{conversation_context or "None"}

Evidence:
{evidence}

Question: {query}
Answer:"""
        try:
            summary = ollama_client.chat([
                {"role": "system", "content": "You are a precise, evidence-grounded research assistant."},
                {"role": "user", "content": prompt},
            ], temperature=0.2)
            return {"status": "success", "summary": summary, "num_chunks_used": len(chunks)}
        except Exception as exc:
            agent_logger.exception("Summarization failed")
            return {"status": "error", "message": str(exc), "summary": ""}
