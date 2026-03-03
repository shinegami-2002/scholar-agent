"""ChromaDB vector store service for paper embeddings."""

import logging
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.config import settings
from app.services.embeddings import get_embeddings

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Wrapper around ChromaDB for storing and querying paper chunks."""

    def __init__(self) -> None:
        persist_dir = Path(settings.chroma_persist_dir)
        persist_dir.mkdir(parents=True, exist_ok=True)

        self._store = Chroma(
            collection_name=settings.chroma_collection_name,
            embedding_function=get_embeddings(),
            persist_directory=str(persist_dir),
        )
        logger.info(
            "ChromaDB initialised — collection=%s, dir=%s",
            settings.chroma_collection_name,
            persist_dir,
        )

    def add_documents(self, docs: list[Document]) -> None:
        """Embed and store a batch of LangChain Documents.

        Each Document should carry metadata (title, url, source, etc.)
        so retrieval results are traceable back to the original paper.
        """
        if not docs:
            logger.warning("add_documents called with empty list — skipping")
            return

        self._store.add_documents(docs)
        logger.info("Added %d documents to vector store", len(docs))

    def search(self, query: str, k: int | None = None) -> list[Document]:
        """Return the top-k most similar documents for *query*.

        Falls back to ``settings.top_k_results`` when *k* is not provided.
        """
        k = k or settings.top_k_results
        results = self._store.similarity_search(query, k=k)
        logger.info("Vector search for '%s' returned %d results", query, len(results))
        return results

    def clear(self) -> None:
        """Delete every document in the collection.

        Useful between searches so stale papers don't pollute results.
        """
        self._store.delete_collection()
        # Re-create the empty collection so subsequent calls still work.
        self._store = Chroma(
            collection_name=settings.chroma_collection_name,
            embedding_function=get_embeddings(),
            persist_directory=str(Path(settings.chroma_persist_dir)),
        )
        logger.info("Vector store cleared")
