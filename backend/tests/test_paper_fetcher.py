"""Tests for PaperFetcher — arXiv and PubMed search with mocked HTTP."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import httpx
import pytest
import respx

from app.services.paper_fetcher import PUBMED_BASE_URL, PaperFetcher

# ---------------------------------------------------------------------------
# PubMed fixtures
# ---------------------------------------------------------------------------

ESEARCH_RESPONSE = {
    "esearchresult": {
        "count": "2",
        "retmax": "2",
        "idlist": ["39000001", "39000002"],
    }
}

EFETCH_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>39000001</PMID>
      <Article>
        <ArticleTitle>Deep Learning for Drug Discovery</ArticleTitle>
        <Abstract>
          <AbstractText>We present a deep learning approach for drug discovery.</AbstractText>
        </Abstract>
        <AuthorList>
          <Author><ForeName>Alice</ForeName><LastName>Wang</LastName></Author>
          <Author><ForeName>Bob</ForeName><LastName>Chen</LastName></Author>
        </AuthorList>
        <Journal>
          <JournalIssue>
            <PubDate><Year>2024</Year><Month>Mar</Month></PubDate>
          </JournalIssue>
        </Journal>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>39000002</PMID>
      <Article>
        <ArticleTitle>Genomics and Machine Learning</ArticleTitle>
        <Abstract>
          <AbstractText>This paper surveys ML applications in genomics.</AbstractText>
        </Abstract>
        <AuthorList>
          <Author><ForeName>Carol</ForeName><LastName>Li</LastName></Author>
        </AuthorList>
        <Journal>
          <JournalIssue>
            <PubDate><Year>2024</Year><Month>Jan</Month><Day>15</Day></PubDate>
          </JournalIssue>
        </Journal>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""


# ---------------------------------------------------------------------------
# PubMed tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_search_pubmed_returns_papers():
    """PubMed esearch + efetch should return PaperResult objects."""
    respx.get(f"{PUBMED_BASE_URL}esearch.fcgi").mock(
        return_value=httpx.Response(200, json=ESEARCH_RESPONSE)
    )
    respx.get(f"{PUBMED_BASE_URL}efetch.fcgi").mock(
        return_value=httpx.Response(200, text=EFETCH_XML)
    )

    fetcher = PaperFetcher()
    papers = await fetcher.search_pubmed("deep learning drug discovery", max_results=2)

    assert len(papers) == 2

    paper_0 = papers[0]
    assert paper_0.title == "Deep Learning for Drug Discovery"
    assert paper_0.source == "pubmed"
    assert "Alice Wang" in paper_0.authors
    assert "Bob Chen" in paper_0.authors
    assert paper_0.url == "https://pubmed.ncbi.nlm.nih.gov/39000001/"
    assert paper_0.published == "2024-Mar"

    paper_1 = papers[1]
    assert paper_1.title == "Genomics and Machine Learning"
    assert paper_1.published == "2024-Jan-15"


@pytest.mark.asyncio
@respx.mock
async def test_search_pubmed_empty_results():
    """PubMed returns empty list when no IDs match."""
    respx.get(f"{PUBMED_BASE_URL}esearch.fcgi").mock(
        return_value=httpx.Response(
            200, json={"esearchresult": {"count": "0", "idlist": []}}
        )
    )

    fetcher = PaperFetcher()
    papers = await fetcher.search_pubmed("qwertyuiop12345", max_results=5)
    assert papers == []


@pytest.mark.asyncio
@respx.mock
async def test_search_pubmed_network_error():
    """PubMed raises on network failure."""
    respx.get(f"{PUBMED_BASE_URL}esearch.fcgi").mock(
        side_effect=httpx.ConnectError("DNS resolution failed")
    )

    fetcher = PaperFetcher()
    with pytest.raises(httpx.ConnectError):
        await fetcher.search_pubmed("deep learning", max_results=5)


# ---------------------------------------------------------------------------
# arXiv tests (mock the arxiv library)
# ---------------------------------------------------------------------------


def _make_mock_arxiv_result(title: str, summary: str, entry_id: str) -> MagicMock:
    """Build a mock arxiv.Result object."""
    result = MagicMock()
    result.title = title
    result.summary = summary
    result.entry_id = entry_id
    result.published = datetime(2024, 1, 15)

    author1 = MagicMock()
    author1.name = "Test Author"
    result.authors = [author1]

    return result


@pytest.mark.asyncio
@patch("app.services.paper_fetcher.arxiv")
async def test_search_arxiv_returns_papers(mock_arxiv_module):
    """arXiv search should return PaperResult objects from mocked library."""
    mock_results = [
        _make_mock_arxiv_result(
            title="AlphaFold2: Protein Structure Prediction",
            summary="We present AlphaFold2 for protein structure prediction.",
            entry_id="https://arxiv.org/abs/2107.00000",
        ),
    ]

    mock_client = MagicMock()
    mock_client.results.return_value = mock_results
    mock_arxiv_module.Client.return_value = mock_client
    mock_arxiv_module.Search = MagicMock()
    mock_arxiv_module.SortCriterion.Relevance = "relevance"

    fetcher = PaperFetcher()
    papers = await fetcher.search_arxiv("protein folding", max_results=5)

    assert len(papers) == 1
    assert papers[0].title == "AlphaFold2: Protein Structure Prediction"
    assert papers[0].source == "arxiv"
    assert papers[0].url == "https://arxiv.org/abs/2107.00000"
    assert papers[0].published == "2024-01-15"
    assert "Test Author" in papers[0].authors


@pytest.mark.asyncio
@patch("app.services.paper_fetcher.arxiv")
async def test_search_arxiv_empty(mock_arxiv_module):
    """arXiv returns empty list when no results match."""
    mock_client = MagicMock()
    mock_client.results.return_value = []
    mock_arxiv_module.Client.return_value = mock_client
    mock_arxiv_module.Search = MagicMock()
    mock_arxiv_module.SortCriterion.Relevance = "relevance"

    fetcher = PaperFetcher()
    papers = await fetcher.search_arxiv("qwertyuiop12345", max_results=5)

    assert papers == []


@pytest.mark.asyncio
@patch("app.services.paper_fetcher.arxiv")
async def test_search_arxiv_exception(mock_arxiv_module):
    """arXiv propagates exceptions from the library."""
    mock_client = MagicMock()
    mock_client.results.side_effect = RuntimeError("arXiv API unreachable")
    mock_arxiv_module.Client.return_value = mock_client
    mock_arxiv_module.Search = MagicMock()
    mock_arxiv_module.SortCriterion.Relevance = "relevance"

    fetcher = PaperFetcher()
    with pytest.raises(RuntimeError, match="arXiv API unreachable"):
        await fetcher.search_arxiv("deep learning", max_results=5)


# ---------------------------------------------------------------------------
# Unified search dispatcher
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
@patch("app.services.paper_fetcher.arxiv")
async def test_search_unified_merges_results(mock_arxiv_module):
    """The unified search() should merge arXiv + PubMed results."""
    # Mock arXiv
    mock_results = [
        _make_mock_arxiv_result(
            title="arXiv Paper",
            summary="An arXiv paper.",
            entry_id="https://arxiv.org/abs/0001.00000",
        ),
    ]
    mock_client = MagicMock()
    mock_client.results.return_value = mock_results
    mock_arxiv_module.Client.return_value = mock_client
    mock_arxiv_module.Search = MagicMock()
    mock_arxiv_module.SortCriterion.Relevance = "relevance"

    # Mock PubMed
    respx.get(f"{PUBMED_BASE_URL}esearch.fcgi").mock(
        return_value=httpx.Response(200, json=ESEARCH_RESPONSE)
    )
    respx.get(f"{PUBMED_BASE_URL}efetch.fcgi").mock(
        return_value=httpx.Response(200, text=EFETCH_XML)
    )

    fetcher = PaperFetcher()
    papers = await fetcher.search("deep learning", sources=["arxiv", "pubmed"], max_results=5)

    # 1 from arXiv + 2 from PubMed = 3
    assert len(papers) == 3
    sources = {p.source for p in papers}
    assert sources == {"arxiv", "pubmed"}


@pytest.mark.asyncio
@respx.mock
@patch("app.services.paper_fetcher.arxiv")
async def test_search_unified_handles_partial_failure(mock_arxiv_module):
    """If one source fails, the other results are still returned."""
    # arXiv will raise
    mock_client = MagicMock()
    mock_client.results.side_effect = RuntimeError("arXiv down")
    mock_arxiv_module.Client.return_value = mock_client
    mock_arxiv_module.Search = MagicMock()
    mock_arxiv_module.SortCriterion.Relevance = "relevance"

    # PubMed will succeed
    respx.get(f"{PUBMED_BASE_URL}esearch.fcgi").mock(
        return_value=httpx.Response(200, json=ESEARCH_RESPONSE)
    )
    respx.get(f"{PUBMED_BASE_URL}efetch.fcgi").mock(
        return_value=httpx.Response(200, text=EFETCH_XML)
    )

    fetcher = PaperFetcher()
    papers = await fetcher.search("deep learning", sources=["arxiv", "pubmed"], max_results=5)

    # Only PubMed results should be returned
    assert len(papers) == 2
    assert all(p.source == "pubmed" for p in papers)
