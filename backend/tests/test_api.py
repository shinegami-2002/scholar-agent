"""Tests for the FastAPI endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import SearchResponse


@pytest.fixture()
def client():
    """FastAPI TestClient for synchronous endpoint testing."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_200(self, client):
        """Health check should return 200 with status healthy."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "scholar-agent"

    def test_health_response_format(self, client):
        """Health response should have exactly the expected keys."""
        response = client.get("/health")
        data = response.json()

        assert set(data.keys()) == {"status", "service"}


class TestSearchEndpoint:
    """Tests for POST /api/search."""

    @patch("app.agents.graph.run_search", new_callable=AsyncMock)
    def test_search_returns_response(self, mock_run_search, client):
        """A valid search request should return a SearchResponse."""
        mock_run_search.return_value = SearchResponse(
            query="transformer architecture",
            answer="Transformers use self-attention mechanisms [1].",
            citations=[
                {"index": 1, "title": "Attention Is All You Need", "url": "https://arxiv.org/abs/1706.03762"}
            ],
            papers=[
                {
                    "title": "Attention Is All You Need",
                    "authors": ["Ashish Vaswani"],
                    "abstract": "We propose the Transformer architecture.",
                    "url": "https://arxiv.org/abs/1706.03762",
                    "source": "arxiv",
                    "published": "2017-06-12",
                }
            ],
            steps=[
                {"node": "router", "status": "completed", "detail": "paper_search", "duration_ms": 50}
            ],
            rewrite_count=0,
        )

        response = client.post(
            "/api/search",
            json={"query": "transformer architecture", "sources": ["arxiv"], "max_results": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "transformer architecture"
        assert "Transformers" in data["answer"]
        assert len(data["citations"]) == 1
        assert len(data["papers"]) == 1
        assert data["rewrite_count"] == 0

    @patch("app.agents.graph.run_search", new_callable=AsyncMock)
    def test_search_calls_run_search_with_correct_args(self, mock_run_search, client):
        """run_search should be called with the request parameters."""
        mock_run_search.return_value = SearchResponse(
            query="BERT",
            answer="BERT is a language model.",
        )

        client.post(
            "/api/search",
            json={"query": "BERT", "sources": ["arxiv", "pubmed"], "max_results": 15},
        )

        mock_run_search.assert_called_once_with(
            query="BERT",
            sources=["arxiv", "pubmed"],
            max_results=15,
        )

    def test_search_empty_query_returns_422(self, client):
        """An empty query string should return 422 validation error."""
        response = client.post(
            "/api/search",
            json={"query": "", "sources": ["arxiv"]},
        )

        assert response.status_code == 422

    def test_search_missing_query_returns_422(self, client):
        """A request without a query field should return 422."""
        response = client.post(
            "/api/search",
            json={"sources": ["arxiv"]},
        )

        assert response.status_code == 422

    @patch("app.agents.graph.run_search", new_callable=AsyncMock)
    def test_search_default_sources(self, mock_run_search, client):
        """When sources are not specified, defaults should be used."""
        mock_run_search.return_value = SearchResponse(
            query="test",
            answer="test answer",
        )

        response = client.post(
            "/api/search",
            json={"query": "test query"},
        )

        assert response.status_code == 200
        call_kwargs = mock_run_search.call_args
        assert call_kwargs.kwargs["sources"] == ["arxiv", "pubmed"]

    def test_search_max_results_out_of_range(self, client):
        """max_results outside 1-50 should return 422."""
        response = client.post(
            "/api/search",
            json={"query": "test", "max_results": 100},
        )
        assert response.status_code == 422

        response = client.post(
            "/api/search",
            json={"query": "test", "max_results": 0},
        )
        assert response.status_code == 422


class TestCORSMiddleware:
    """Test that CORS headers are present."""

    def test_cors_allows_localhost(self, client):
        """The frontend origin should be allowed."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # FastAPI CORS middleware should respond to preflight
        assert response.status_code in (200, 204)
