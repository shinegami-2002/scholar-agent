"""LangGraph state graph for the ScholarAgent research pipeline.

Graph topology:

  START -> router
  router -> retriever       (if paper_search)
  router -> generator       (if general)
  retriever -> grader
  grader -> generator       (if docs are relevant OR retries exhausted)
  grader -> rewriter        (if docs irrelevant AND retries remaining)
  rewriter -> retriever     (loop back for another search)
  generator -> hallucination_checker
  hallucination_checker -> synthesizer  (if score < threshold)
  hallucination_checker -> generator    (retry once if hallucinated)
  synthesizer -> END
"""

import logging

from langgraph.graph import END, START, StateGraph

from app.agents.nodes.generator import generate_answer
from app.agents.nodes.grader import grade_documents
from app.agents.nodes.hallucination_checker import check_hallucination
from app.agents.nodes.retriever import retrieve_papers
from app.agents.nodes.rewriter import rewrite_query
from app.agents.nodes.router import route_query
from app.agents.nodes.synthesizer import synthesize_response
from app.agents.state import AgentState
from app.config import settings
from app.models.schemas import AgentStep, Citation, PaperResult, SearchResponse

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Conditional edge functions
# ---------------------------------------------------------------------------

def _route_after_router(state: AgentState) -> str:
    """Decide whether to search papers or go straight to generation."""
    classification = state.get("classification", "paper_search")
    if classification == "general":
        return "generator"
    return "retriever"


def _route_after_grader(state: AgentState) -> str:
    """If graded docs are empty and we have retries left, rewrite; otherwise generate."""
    graded = state.get("graded_documents", [])
    rewrite_count = state.get("rewrite_count", 0)
    max_retries = settings.max_rewrite_retries

    if graded:
        return "generator"

    if rewrite_count < max_retries:
        logger.info(
            "No relevant docs — rewriting query (attempt %d/%d)",
            rewrite_count + 1,
            max_retries,
        )
        return "rewriter"

    # Retries exhausted — generate with whatever we have
    logger.warning("Rewrite retries exhausted (%d/%d) — generating anyway", rewrite_count, max_retries)
    return "generator"


def _route_after_hallucination(state: AgentState) -> str:
    """If hallucination score is above threshold and this is the first check, retry generation."""
    score = state.get("hallucination_score", 0.0)
    threshold = settings.hallucination_threshold

    # Count how many times generator has already run
    generator_runs = sum(
        1 for step in state.get("steps", []) if step.get("node") == "generator"
    )

    if score >= threshold and generator_runs <= 1:
        logger.info(
            "Hallucination score %.2f >= threshold %.2f — retrying generation",
            score,
            threshold,
        )
        return "generator"

    return "synthesizer"


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """Construct and compile the ScholarAgent state graph.

    Returns the compiled graph ready to be invoked.
    """
    graph = StateGraph(AgentState)

    # -- Add nodes --
    graph.add_node("router", route_query)
    graph.add_node("retriever", retrieve_papers)
    graph.add_node("grader", grade_documents)
    graph.add_node("rewriter", rewrite_query)
    graph.add_node("generator", generate_answer)
    graph.add_node("hallucination_checker", check_hallucination)
    graph.add_node("synthesizer", synthesize_response)

    # -- Add edges --
    graph.add_edge(START, "router")

    graph.add_conditional_edges(
        "router",
        _route_after_router,
        {"retriever": "retriever", "generator": "generator"},
    )

    graph.add_edge("retriever", "grader")

    graph.add_conditional_edges(
        "grader",
        _route_after_grader,
        {"generator": "generator", "rewriter": "rewriter"},
    )

    graph.add_edge("rewriter", "retriever")

    graph.add_edge("generator", "hallucination_checker")

    graph.add_conditional_edges(
        "hallucination_checker",
        _route_after_hallucination,
        {"synthesizer": "synthesizer", "generator": "generator"},
    )

    graph.add_edge("synthesizer", END)

    return graph.compile()


# ---------------------------------------------------------------------------
# High-level runner
# ---------------------------------------------------------------------------

async def run_search(
    query: str,
    sources: list[str] | None = None,
    max_results: int | None = None,
) -> SearchResponse:
    """Execute the full ScholarAgent pipeline and return a SearchResponse.

    This is the main entry point called by the API layer.
    """
    if sources is None:
        sources = ["arxiv", "pubmed"]
    if max_results is None:
        max_results = settings.max_papers

    initial_state: AgentState = {
        "query": query,
        "sources": sources,
        "max_results": max_results,
        "documents": [],
        "graded_documents": [],
        "rewrite_count": 0,
        "answer": "",
        "hallucination_score": 0.0,
        "steps": [],
        "citations": [],
    }

    compiled_graph = build_graph()

    # Use ainvoke for async context (called from async FastAPI endpoint)
    final_state = await compiled_graph.ainvoke(initial_state)

    # --- Build SearchResponse from final state ---
    papers = [
        PaperResult(**doc)
        for doc in final_state.get("graded_documents", [])
    ]

    citations = [
        Citation(**c)
        for c in final_state.get("citations", [])
    ]

    steps = [
        AgentStep(**s)
        for s in final_state.get("steps", [])
    ]

    return SearchResponse(
        query=final_state.get("query", query),
        answer=final_state.get("answer", ""),
        citations=citations,
        papers=papers,
        steps=steps,
        rewrite_count=final_state.get("rewrite_count", 0),
    )
