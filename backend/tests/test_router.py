"""Tests for the Router node — query classification."""

from __future__ import annotations

from unittest.mock import patch

from langchain_core.messages import AIMessage


class TestRouteQuery:
    """Test that route_query correctly classifies queries."""

    @patch("app.agents.nodes.router.get_llm")
    def test_paper_search_classification(self, mock_get_llm, sample_state):
        """A research query should be classified as 'paper_search'."""
        from app.agents.nodes.router import route_query

        mock_llm = mock_get_llm.return_value
        mock_llm.invoke.return_value = AIMessage(content="paper_search")

        state = {**sample_state, "query": "transformer architecture for protein folding"}
        result = route_query(state)

        assert result["classification"] == "paper_search"
        assert len(result["steps"]) == 1
        assert result["steps"][0]["node"] == "router"
        assert result["steps"][0]["status"] == "completed"
        assert "paper_search" in result["steps"][0]["detail"]

    @patch("app.agents.nodes.router.get_llm")
    def test_general_classification(self, mock_get_llm, sample_state):
        """A casual greeting should be classified as 'general'."""
        from app.agents.nodes.router import route_query

        mock_llm = mock_get_llm.return_value
        mock_llm.invoke.return_value = AIMessage(content="general")

        state = {**sample_state, "query": "hello how are you"}
        result = route_query(state)

        assert result["classification"] == "general"
        assert "general" in result["steps"][-1]["detail"]

    @patch("app.agents.nodes.router.get_llm")
    def test_fuzzy_paper_classification(self, mock_get_llm, sample_state):
        """If the LLM returns a variant like 'paper_search ', it should normalise."""
        from app.agents.nodes.router import route_query

        mock_llm = mock_get_llm.return_value
        mock_llm.invoke.return_value = AIMessage(content="  Paper_Search  ")

        state = {**sample_state, "query": "latest NLP research"}
        result = route_query(state)

        assert result["classification"] == "paper_search"

    @patch("app.agents.nodes.router.get_llm")
    def test_unexpected_response_defaults_to_general(self, mock_get_llm, sample_state):
        """If the LLM returns something unexpected, it should default to 'general'."""
        from app.agents.nodes.router import route_query

        mock_llm = mock_get_llm.return_value
        mock_llm.invoke.return_value = AIMessage(content="I don't understand")

        state = {**sample_state, "query": "what is the meaning of life"}
        result = route_query(state)

        assert result["classification"] == "general"

    @patch("app.agents.nodes.router.get_llm")
    def test_preserves_existing_steps(self, mock_get_llm, sample_state):
        """Router should append to existing steps, not replace them."""
        from app.agents.nodes.router import route_query

        mock_llm = mock_get_llm.return_value
        mock_llm.invoke.return_value = AIMessage(content="general")

        existing_step = {"node": "previous", "status": "completed", "detail": "test"}
        state = {**sample_state, "steps": [existing_step]}
        result = route_query(state)

        assert len(result["steps"]) == 2
        assert result["steps"][0] == existing_step
        assert result["steps"][1]["node"] == "router"

    @patch("app.agents.nodes.router.get_llm")
    def test_step_has_duration(self, mock_get_llm, sample_state):
        """Router step should include a non-negative duration_ms."""
        from app.agents.nodes.router import route_query

        mock_llm = mock_get_llm.return_value
        mock_llm.invoke.return_value = AIMessage(content="general")

        result = route_query(sample_state)

        step = result["steps"][-1]
        assert "duration_ms" in step
        assert isinstance(step["duration_ms"], int)
        assert step["duration_ms"] >= 0
