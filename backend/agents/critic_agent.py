"""Evidence and hallucination critic agent."""
from llm_client import ollama_client
from utils.logger import agent_logger


class CriticAgent:
    name = "Critic Agent"

    def critique(self, query: str, summary: str, chunks: list[str]):
        if not summary:
            return {"status": "error", "message": "No draft to critique", "critique": "", "suggestions": []}
        prompt = f"""Audit this draft against the evidence. Check factual support, citation
alignment, missing relevant facts, and whether uncertainty is disclosed.
Return exactly these headings:
STRENGTHS:
GAPS:
SUGGESTIONS:

Question: {query}
Draft: {summary}
Evidence: {' '.join(chunks)}"""
        try:
            critique = ollama_client.chat([
                {"role": "system", "content": "You are a strict RAG quality auditor."},
                {"role": "user", "content": prompt},
            ], temperature=0.1)
            gaps = critique.partition("GAPS:")[2].partition("SUGGESTIONS:")[0].strip().lower()
            has_gaps = bool(gaps) and not gaps.startswith(("none", "no gaps"))
            suggestions = [line.strip(" -*") for line in critique.partition("SUGGESTIONS:")[2].splitlines() if line.strip()]
            return {"status": "success", "critique": critique, "suggestions": suggestions[:5], "has_gaps": has_gaps}
        except Exception as exc:
            agent_logger.exception("Critique failed")
            return {"status": "error", "message": str(exc), "critique": "", "suggestions": []}
