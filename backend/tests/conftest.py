"""Shared fixtures for ScholarAgent backend tests."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Pre-import mock for langchain_chroma
#
# ChromaDB's Settings class triggers a pydantic-v1 ConfigError when imported
# under pydantic v2.  We inject a fake ``langchain_chroma`` module into
# ``sys.modules`` BEFORE any application code is imported so the
# ``from langchain_chroma import Chroma`` in vector_store.py resolves to a
# harmless MagicMock instead of the real (broken) class.
# ---------------------------------------------------------------------------
if "langchain_chroma" not in sys.modules:
    _mock_langchain_chroma = MagicMock()
    sys.modules["langchain_chroma"] = _mock_langchain_chroma

import pytest
from langchain_core.messages import AIMessage


@pytest.fixture()
def mock_llm():
    """Return a mock LLM that produces a configurable AIMessage.

    By default the mock returns an AIMessage with content "mock response".
    Tests can override via ``mock_llm.invoke.return_value``.
    """
    llm = MagicMock()
    llm.invoke.return_value = AIMessage(content="mock response")
    return llm


@pytest.fixture()
def sample_papers() -> list[dict]:
    """A list of PaperResult-compatible dicts for testing."""
    return [
        {
            "title": "Attention Is All You Need",
            "authors": ["Ashish Vaswani", "Noam Shazeer"],
            "abstract": (
                "The dominant sequence transduction models are based on complex "
                "recurrent or convolutional neural networks. We propose a new simple "
                "network architecture, the Transformer, based solely on attention mechanisms."
            ),
            "url": "https://arxiv.org/abs/1706.03762",
            "source": "arxiv",
            "published": "2017-06-12",
            "relevance_score": None,
        },
        {
            "title": "BERT: Pre-training of Deep Bidirectional Transformers",
            "authors": ["Jacob Devlin", "Ming-Wei Chang"],
            "abstract": (
                "We introduce a new language representation model called BERT, which "
                "stands for Bidirectional Encoder Representations from Transformers."
            ),
            "url": "https://arxiv.org/abs/1810.04805",
            "source": "arxiv",
            "published": "2018-10-11",
            "relevance_score": None,
        },
        {
            "title": "Clinical applications of deep learning in oncology",
            "authors": ["Jane Doe", "John Smith"],
            "abstract": (
                "Deep learning has shown remarkable success in medical imaging and "
                "clinical diagnosis for cancer detection and treatment planning."
            ),
            "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
            "source": "pubmed",
            "published": "2023-01-15",
            "relevance_score": None,
        },
    ]


@pytest.fixture()
def sample_state(sample_papers) -> dict:
    """A realistic AgentState dict for node-level tests."""
    return {
        "query": "transformer architecture for protein folding",
        "sources": ["arxiv", "pubmed"],
        "max_results": 10,
        "documents": sample_papers,
        "graded_documents": [],
        "rewrite_count": 0,
        "answer": "",
        "hallucination_score": 0.0,
        "steps": [],
        "citations": [],
    }
