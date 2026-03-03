"""Agent state definition for the ScholarAgent LangGraph pipeline."""

from typing import TypedDict


class AgentState(TypedDict, total=False):
    """Shared state that flows through every node in the research graph.

    Fields marked ``total=False`` are optional — nodes progressively
    populate them as the graph executes.
    """

    # --- Input ---
    query: str
    sources: list[str]          # e.g. ["arxiv", "pubmed"]
    max_results: int

    # --- Retrieval ---
    documents: list[dict]       # raw PaperResult dicts from PaperFetcher
    graded_documents: list[dict]  # only docs that pass relevance grading

    # --- Generation ---
    answer: str
    citations: list[dict]       # Citation dicts with index, title, url
    hallucination_score: float  # 0.0 = fully grounded, 1.0 = hallucinated

    # --- Control ---
    classification: str         # "paper_search" or "general" (set by router)
    rewrite_count: int          # number of query rewrites performed (default 0)
    steps: list[dict]           # AgentStep dicts — execution trace
