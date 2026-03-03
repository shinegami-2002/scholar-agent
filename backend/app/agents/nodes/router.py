"""Router node — classifies the user query as paper_search or general."""

import logging
import time

from langchain_core.messages import HumanMessage

from app.agents.state import AgentState
from app.services.llm_provider import extract_text, invoke_with_retry

logger = logging.getLogger(__name__)

_ROUTER_PROMPT = (
    "You are a query classifier for a research assistant. "
    "Given the user query below, respond with EXACTLY one word:\n"
    "- 'paper_search' if the query is asking about academic papers, research findings, "
    "scientific topics, literature reviews, or anything that would benefit from "
    "searching arXiv or PubMed.\n"
    "- 'general' if the query is casual conversation, greetings, or unrelated to "
    "academic research.\n\n"
    "Query: {query}\n\n"
    "Classification:"
)


def route_query(state: AgentState) -> AgentState:
    """Classify the user query intent and record the routing decision."""
    start = time.perf_counter()
    query = state["query"]

    prompt = _ROUTER_PROMPT.format(query=query)
    response = invoke_with_retry([HumanMessage(content=prompt)])

    classification = extract_text(response).strip().lower()
    # Normalise — accept minor variations from the LLM
    if "paper" in classification or "search" in classification:
        classification = "paper_search"
    else:
        classification = "general"

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    logger.info("Query routed as '%s' in %dms", classification, elapsed_ms)

    steps = list(state.get("steps", []))
    steps.append({
        "node": "router",
        "status": "completed",
        "detail": f"Classified as '{classification}'",
        "duration_ms": elapsed_ms,
    })

    return {**state, "classification": classification, "steps": steps}
