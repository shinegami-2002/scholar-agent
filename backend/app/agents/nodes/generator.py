"""Generator node — produces a cited answer from graded documents."""

import logging
import time

from langchain_core.messages import HumanMessage

from app.agents.state import AgentState
from app.services.llm_provider import extract_text, invoke_with_retry

logger = logging.getLogger(__name__)

_GENERATE_PROMPT = (
    "You are a research assistant. Using ONLY the provided paper abstracts, "
    "write a comprehensive answer to the user's query. "
    "Cite papers inline using [1], [2], etc. corresponding to the paper numbers below.\n\n"
    "If the provided papers are insufficient, say so honestly rather than fabricating information.\n\n"
    "Query: {query}\n\n"
    "{papers_context}\n\n"
    "Answer:"
)

_GENERAL_PROMPT = (
    "You are ScholarAgent, a research assistant that helps users find and "
    "understand academic papers. The user sent a general (non-research) message. "
    "Respond helpfully and concisely. Mention that you can search arXiv and "
    "PubMed for research papers.\n\n"
    "User: {query}\n\n"
    "Response:"
)


def _build_papers_context(documents: list[dict]) -> str:
    """Format a numbered list of paper abstracts for the generation prompt."""
    if not documents:
        return "No relevant papers found."

    parts = []
    for i, doc in enumerate(documents, start=1):
        title = doc.get("title", "Untitled")
        abstract = doc.get("abstract", "No abstract available.")[:1500]
        url = doc.get("url", "")
        parts.append(f"[{i}] {title}\nURL: {url}\nAbstract: {abstract}")
    return "\n\n".join(parts)


def _extract_citations(documents: list[dict]) -> list[dict]:
    """Build citation dicts from the graded document list."""
    citations = []
    for i, doc in enumerate(documents, start=1):
        citations.append({
            "index": i,
            "title": doc.get("title", "Untitled"),
            "url": doc.get("url", ""),
        })
    return citations


def generate_answer(state: AgentState) -> AgentState:
    """Generate a cited answer from graded documents, or a general response."""
    start = time.perf_counter()

    query = state["query"]
    classification = state.get("classification", "paper_search")
    graded_documents = state.get("graded_documents", [])
    if classification == "general":
        prompt = _GENERAL_PROMPT.format(query=query)
        response = invoke_with_retry([HumanMessage(content=prompt)])
        answer = extract_text(response).strip()
        citations: list[dict] = []
    else:
        papers_context = _build_papers_context(graded_documents)
        prompt = _GENERATE_PROMPT.format(query=query, papers_context=papers_context)
        response = invoke_with_retry([HumanMessage(content=prompt)])
        answer = extract_text(response).strip()
        citations = _extract_citations(graded_documents)

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    logger.info("Answer generated in %dms (%d chars)", elapsed_ms, len(answer))

    steps = list(state.get("steps", []))
    steps.append({
        "node": "generator",
        "status": "completed",
        "detail": f"Generated answer with {len(citations)} citations",
        "duration_ms": elapsed_ms,
    })

    return {**state, "answer": answer, "citations": citations, "steps": steps}
