"""Retriever node — fetches papers from external APIs and indexes them in ChromaDB."""

import asyncio
import logging
import time

from langchain_core.documents import Document

from app.agents.state import AgentState
from app.config import settings
from app.services.paper_fetcher import PaperFetcher
from app.services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from sync context, handling nested event loops."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    # If there's already a running loop (e.g., called from async FastAPI context),
    # use a new thread to avoid "cannot run nested event loop" error
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(asyncio.run, coro)
        return future.result()


def retrieve_papers(state: AgentState) -> AgentState:
    """Search arXiv/PubMed, embed results in ChromaDB, and retrieve top-k."""
    start = time.perf_counter()

    query = state["query"]
    sources = state.get("sources", ["arxiv", "pubmed"])
    max_results = state.get("max_results", settings.max_papers)

    # --- 1. Fetch papers from external APIs ---
    fetcher = PaperFetcher()
    raw_papers = _run_async(
        fetcher.search(query=query, sources=sources, max_results=max_results)
    )
    logger.info("PaperFetcher returned %d papers", len(raw_papers))

    if not raw_papers:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        steps = list(state.get("steps", []))
        steps.append({
            "node": "retriever",
            "status": "completed",
            "detail": "No papers found from external APIs",
            "duration_ms": elapsed_ms,
        })
        return {**state, "documents": [], "steps": steps}

    # --- 2. Convert PaperResult objects to dicts for downstream nodes ---
    paper_dicts = [p.model_dump() for p in raw_papers]

    # --- 3. Convert to LangChain Documents and index in ChromaDB ---
    vector_store = VectorStoreService()
    vector_store.clear()

    lc_docs = [
        Document(
            page_content=paper["abstract"],
            metadata={
                "title": paper["title"],
                "authors": ", ".join(paper["authors"]),
                "url": paper["url"],
                "source": paper["source"],
                "published": paper.get("published") or "",
            },
        )
        for paper in paper_dicts
        if paper.get("abstract")
    ]

    vector_store.add_documents(lc_docs)

    # --- 4. Retrieve top-k most relevant via similarity search ---
    top_k = settings.top_k_results
    retrieved = vector_store.search(query, k=top_k)

    documents = []
    for doc in retrieved:
        meta = doc.metadata
        documents.append({
            "title": meta.get("title", ""),
            "authors": [a.strip() for a in meta.get("authors", "").split(",") if a.strip()],
            "abstract": doc.page_content,
            "url": meta.get("url", ""),
            "source": meta.get("source", ""),
            "published": meta.get("published"),
            "relevance_score": None,
        })

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    logger.info("Retrieved %d papers from vector store in %dms", len(documents), elapsed_ms)

    steps = list(state.get("steps", []))
    steps.append({
        "node": "retriever",
        "status": "completed",
        "detail": f"Fetched {len(raw_papers)} papers, retrieved top {len(documents)}",
        "duration_ms": elapsed_ms,
    })

    return {**state, "documents": documents, "steps": steps}
