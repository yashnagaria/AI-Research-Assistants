"""Final answer editing agent."""
from llm_client import ollama_client
from utils.logger import agent_logger


class EditorAgent:
    name = "Editor Agent"

    def edit(self, query: str, summary: str, critique: str, chunks: list[str]):
        prompt = f"""Revise the draft using the audit. Use only the evidence, preserve valid
[n] citations, remove unsupported claims, and clearly state evidence gaps.

Question: {query}
Draft: {summary}
Audit: {critique}
Evidence: {' '.join(chunks)}
Final answer:"""
        try:
            answer = ollama_client.chat([
                {"role": "system", "content": "You are the final editor of a grounded research report."},
                {"role": "user", "content": prompt},
            ], temperature=0.2)
            return {"status": "success", "final_answer": answer, "editing_applied": True}
        except Exception as exc:
            agent_logger.exception("Editing failed; returning draft")
            return {"status": "warning", "message": str(exc), "final_answer": summary, "editing_applied": False}
