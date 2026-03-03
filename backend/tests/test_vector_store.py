"""Tests for VectorStoreService with mocked ChromaDB.

The real ``langchain_chroma.Chroma`` is never imported — it is replaced by a
MagicMock in ``conftest.py`` to avoid the pydantic-v1 ``ConfigError`` that
ChromaDB's Settings class triggers.  Here we configure that global mock so
that it behaves like a minimal vector store (add / search / delete).
"""

from __future__ import annotations

import tempfile
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document


@pytest.fixture()
def vector_store():
    """Create a VectorStoreService backed by a fake in-memory Chroma mock.

    The ``langchain_chroma`` module was already replaced by a MagicMock in
    conftest.py.  Here we configure its ``Chroma`` attribute so that
    ``Chroma(...)`` returns a mock instance with working add / search / delete.
    """
    # Shared storage that the mock Chroma instance reads/writes
    stored_docs: list[Document] = []

    def _add_documents(docs):
        stored_docs.extend(docs)

    def _similarity_search(query, k=3):
        return stored_docs[:k]

    def _delete_collection():
        stored_docs.clear()

    # Build a mock Chroma *instance*
    mock_chroma_instance = MagicMock()
    mock_chroma_instance.add_documents.side_effect = _add_documents
    mock_chroma_instance.similarity_search.side_effect = _similarity_search
    mock_chroma_instance.delete_collection.side_effect = _delete_collection

    # Configure the global langchain_chroma mock's Chroma attribute
    mock_chroma_cls = MagicMock(return_value=mock_chroma_instance)

    with tempfile.TemporaryDirectory() as tmpdir:
        with (
            patch("app.services.vector_store.settings") as mock_settings,
            patch("app.services.vector_store.get_embeddings", return_value=MagicMock()),
        ):
            mock_settings.chroma_persist_dir = tmpdir
            mock_settings.chroma_collection_name = "test_collection"
            mock_settings.top_k_results = 3

            # Temporarily set the Chroma class on the already-imported module
            # so VectorStoreService.__init__ sees our configured mock.
            import app.services.vector_store as vs_module

            original_chroma = vs_module.Chroma
            vs_module.Chroma = mock_chroma_cls
            try:
                store = vs_module.VectorStoreService()
                yield store
            finally:
                vs_module.Chroma = original_chroma


@pytest.fixture()
def sample_docs() -> list[Document]:
    """LangChain Document objects for vector store tests."""
    return [
        Document(
            page_content="Transformer models use self-attention mechanisms for sequence transduction.",
            metadata={"title": "Attention Is All You Need", "source": "arxiv", "url": "https://arxiv.org/abs/1706.03762"},
        ),
        Document(
            page_content="BERT uses bidirectional training of Transformer for language understanding.",
            metadata={"title": "BERT Paper", "source": "arxiv", "url": "https://arxiv.org/abs/1810.04805"},
        ),
        Document(
            page_content="Convolutional neural networks have been widely used in image classification tasks.",
            metadata={"title": "CNN for Image Recognition", "source": "pubmed", "url": "https://pubmed.ncbi.nlm.nih.gov/11111/"},
        ),
        Document(
            page_content="Reinforcement learning enables agents to learn optimal policies through trial and error.",
            metadata={"title": "RL Survey", "source": "arxiv", "url": "https://arxiv.org/abs/2001.00001"},
        ),
    ]


class TestVectorStoreAddDocuments:
    """Tests for add_documents method."""

    def test_add_documents_stores_successfully(self, vector_store, sample_docs):
        """Adding documents should not raise and should be searchable afterwards."""
        vector_store.add_documents(sample_docs)

        results = vector_store.search("transformer attention", k=2)
        assert len(results) > 0

    def test_add_empty_list_is_noop(self, vector_store):
        """Passing an empty list should not raise."""
        vector_store.add_documents([])  # should log warning but not crash

        results = vector_store.search("anything", k=3)
        assert len(results) == 0


class TestVectorStoreSearch:
    """Tests for search method."""

    def test_search_returns_documents(self, vector_store, sample_docs):
        """Search should return Document objects with metadata."""
        vector_store.add_documents(sample_docs)

        results = vector_store.search("self-attention transformer", k=2)
        assert len(results) <= 2

        for doc in results:
            assert isinstance(doc, Document)
            assert doc.page_content  # not empty
            assert "title" in doc.metadata

    def test_search_respects_k(self, vector_store, sample_docs):
        """Search should return at most k results."""
        vector_store.add_documents(sample_docs)

        results = vector_store.search("machine learning", k=1)
        assert len(results) == 1

    def test_search_empty_store(self, vector_store):
        """Searching an empty store should return an empty list."""
        results = vector_store.search("transformer", k=3)
        assert results == []


class TestVectorStoreClear:
    """Tests for clear method."""

    def test_clear_removes_all_documents(self, vector_store, sample_docs):
        """After clear(), the store should be empty."""
        vector_store.add_documents(sample_docs)

        # Verify documents exist
        results_before = vector_store.search("transformer", k=5)
        assert len(results_before) > 0

        # Clear and verify empty
        vector_store.clear()

        results_after = vector_store.search("transformer", k=5)
        assert len(results_after) == 0

    def test_clear_allows_re_adding(self, vector_store, sample_docs):
        """After clear(), new documents can be added and searched."""
        vector_store.add_documents(sample_docs)
        vector_store.clear()

        new_docs = [
            Document(
                page_content="Graph neural networks for molecular property prediction.",
                metadata={"title": "GNN Paper", "source": "arxiv", "url": "https://arxiv.org/abs/2222.00000"},
            )
        ]
        vector_store.add_documents(new_docs)

        results = vector_store.search("graph neural network", k=3)
        assert len(results) == 1
        assert results[0].metadata["title"] == "GNN Paper"
