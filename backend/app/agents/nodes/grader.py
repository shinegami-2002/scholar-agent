"""Grader node — LLM judges whether each retrieved document is relevant to the query."""

import logging
import time

from langchain_core.messages import HumanMessage

from app.agents.state import AgentState
from app.services.llm_provider import extract_text, invoke_with_retry

logger = logging.getLogger(__name__)

_GRADER_PROMPT = (
    "You are a relevance grader for a research assistant. "
    "Given a user query and a list of paper abstracts, decide which papers are relevant.\n\n"
    "For EACH paper, respond with its number and 'yes' or 'no' on a separate line.\n"
    "Format: 1: yes\n2: no\n3: yes\n\n"
    "Be generous — mark a paper as relevant if it is even partially related to the query.\n\n"
    "Query: {query}\n\n"
    "{papers_block}\n\n"
    "Relevance verdicts:"
)


def grade_documents(state: AgentState) -> AgentState:
    """Grade each retrieved document for relevance in a single batched LLM call."""
    start = time.perf_counter()

    query = state["query"]
    documents = state.get("documents", [])

    if not documents:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        steps = list(state.get("steps", []))
        steps.append({
            "node": "grader",
            "status": "completed",
            "detail": "0/0 documents relevant",
            "duration_ms": elapsed_ms,
        })
        return {**state, "graded_documents": [], "steps": steps}

    # Build a single prompt with all papers
    papers_block = ""
    for i, doc in enumerate(documents, 1):
        title = doc.get("title", "Untitled")
        abstract = doc.get("abstract", "")[:1000]
        papers_block += f"Paper {i}: {title}\nAbstract: {abstract}\n\n"

    prompt = _GRADER_PROMPT.format(query=query, papers_block=papers_block)
    response = invoke_with_retry([HumanMessage(content=prompt)])
    verdict_text = extract_text(response).strip().lower()

    # Parse verdicts
    graded: list[dict] = []
    for i, doc in enumerate(documents, 1):
        # Look for "i: yes" or "i:yes" patterns
        import re
        pattern = rf"\b{i}\s*:\s*(yes|no)\b"
        match = re.search(pattern, verdict_text)
        if match and match.group(1) == "yes":
            graded.append(doc)
            logger.debug("RELEVANT: %s", doc.get("title", "")[:80])
        else:
            logger.debug("IRRELEVANT: %s", doc.get("title", "")[:80])

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    logger.info(
        "Graded %d docs → %d relevant in %dms",
        len(documents),
        len(graded),
        elapsed_ms,
    )

    steps = list(state.get("steps", []))
    steps.append({
        "node": "grader",
        "status": "completed",
        "detail": f"{len(graded)}/{len(documents)} documents relevant",
        "duration_ms": elapsed_ms,
    })

    return {**state, "graded_documents": graded, "steps": steps}
