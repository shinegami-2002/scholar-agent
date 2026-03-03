"""Singleton embedding model backed by HuggingFace sentence-transformers."""

import logging

from langchain_community.embeddings import HuggingFaceEmbeddings

from app.config import settings

logger = logging.getLogger(__name__)

_embeddings_instance: HuggingFaceEmbeddings | None = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """Return a cached HuggingFaceEmbeddings instance.

    The model is loaded once on first call and reused for the lifetime
    of the process, avoiding repeated downloads and GPU/CPU init overhead.
    """
    global _embeddings_instance  # noqa: PLW0603

    if _embeddings_instance is None:
        logger.info("Loading embedding model: %s", settings.embedding_model)
        _embeddings_instance = HuggingFaceEmbeddings(
            model_name=settings.embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info("Embedding model loaded successfully")

    return _embeddings_instance
