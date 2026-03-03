"""Rewriter node — rewrites the query for better search results when grading fails."""

import logging
import time

from langchain_core.messages import HumanMessage

from app.agents.state import AgentState
from app.services.llm_provider import extract_text, invoke_with_retry

logger = logging.getLogger(__name__)

_REWRITE_PROMPT = (
    "You are a research query optimizer. The original query did not return "
    "sufficiently relevant academic papers. Rewrite the query to improve "
    "search results from arXiv and PubMed.\n\n"
    "Rules:\n"
    "- Keep the core research intent\n"
    "- Use more specific technical terms or synonyms\n"
    "- Expand abbreviations if present\n"
    "- Output ONLY the rewritten query, nothing else\n\n"
    "Original query: {query}\n\n"
    "Rewritten query:"
)


def rewrite_query(state: AgentState) -> AgentState:
    """Rewrite the query using an LLM and increment the rewrite counter."""
    start = time.perf_counter()

    original_query = state["query"]
    prompt = _REWRITE_PROMPT.format(query=original_query)
    response = invoke_with_retry([HumanMessage(content=prompt)])

    new_query = extract_text(response).strip().strip('"').strip("'")
    rewrite_count = state.get("rewrite_count", 0) + 1

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    logger.info(
        "Query rewritten (attempt %d): '%s' -> '%s' in %dms",
        rewrite_count,
        original_query[:80],
        new_query[:80],
        elapsed_ms,
    )

    steps = list(state.get("steps", []))
    steps.append({
        "node": "rewriter",
        "status": "completed",
        "detail": f"Rewrite #{rewrite_count}: '{new_query[:100]}'",
        "duration_ms": elapsed_ms,
    })

    return {
        **state,
        "query": new_query,
        "rewrite_count": rewrite_count,
        "steps": steps,
    }
