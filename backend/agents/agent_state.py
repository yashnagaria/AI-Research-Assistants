"""
LangGraph State Definition for Multi-Agent Workflow
"""
from typing import Any, TypedDict, List, Optional


class AgentState(TypedDict):
    """
    State object passed between agents in the workflow

    This state is maintained throughout the entire agent pipeline
    and each agent can read from and write to it.
    """

    # Input
    query: str                          # User's question
    top_k: int                          # Number of chunks to retrieve
    source: Optional[str]               # Document source filter (legacy)
    doc_ids: Optional[List[str]]        # Phase 5: Document IDs to search
    use_multi_doc: bool                 # Phase 5: Use multi-doc store
    doc_store: Optional[Any]            # MultiDocumentStore to search (None = shared global store)
    conversation_context: str           # Previous conversation history
    research_mode: str                  # documents, web, or hybrid

    # Research Agent Output
    chunks: List[str]                   # Retrieved text chunks
    sources: List[str]                  # Source documents for chunks
    num_chunks_found: int               # Number of chunks retrieved
    searched_docs: List[str]            # Phase 5: Documents that were searched
    web_sources: List[dict]              # Structured DuckDuckGo results

    # Summarizer Agent Output
    initial_summary: str                # First draft answer

    # Critic Agent Output
    critique: str                       # Quality evaluation
    has_gaps: bool                      # Whether answer needs improvement
    suggestions: List[str]              # Improvement suggestions

    # Editor Agent Output
    final_answer: str                   # Polished final answer
    editing_applied: bool               # Whether editing was needed

    # Workflow Metadata
    workflow_log: List[str]             # Progress logs (simple strings)
    status: str                         # Current workflow status
    error_message: Optional[str]        # Error details if any

    # Agent execution flags
    research_complete: bool
    summary_complete: bool
    critique_complete: bool
    editor_complete: bool
