"""Async paper fetcher for arXiv and PubMed."""

from __future__ import annotations

import asyncio
import logging
from xml.etree import ElementTree

import arxiv
import httpx

from app.config import settings
from app.models.schemas import PaperResult

logger = logging.getLogger(__name__)

PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"


class PaperFetcher:
    """Fetches academic papers from arXiv and PubMed."""

    # ------------------------------------------------------------------
    # arXiv
    # ------------------------------------------------------------------

    async def search_arxiv(
        self,
        query: str,
        max_results: int | None = None,
    ) -> list[PaperResult]:
        """Search arXiv using the ``arxiv`` library.

        The library is synchronous, so we delegate to a thread to keep
        the event loop free.
        """
        max_results = max_results or settings.max_papers

        def _sync_search() -> list[PaperResult]:
            client = arxiv.Client()
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance,
            )
            papers: list[PaperResult] = []
            for result in client.results(search):
                papers.append(
                    PaperResult(
                        title=result.title,
                        authors=[a.name for a in result.authors],
                        abstract=result.summary,
                        url=result.entry_id,
                        source="arxiv",
                        published=(
                            result.published.strftime("%Y-%m-%d")
                            if result.published
                            else None
                        ),
                    )
                )
            return papers

        papers = await asyncio.to_thread(_sync_search)
        logger.info("arXiv returned %d papers for '%s'", len(papers), query)
        return papers

    # ------------------------------------------------------------------
    # PubMed
    # ------------------------------------------------------------------

    async def search_pubmed(
        self,
        query: str,
        max_results: int | None = None,
    ) -> list[PaperResult]:
        """Search PubMed via the NCBI E-utilities REST API.

        Workflow: esearch (get IDs) -> efetch (get full records as XML).
        """
        max_results = max_results or settings.max_papers

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1 — esearch: get matching PubMed IDs
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
            }
            search_resp = await client.get(
                f"{PUBMED_BASE_URL}esearch.fcgi", params=search_params
            )
            search_resp.raise_for_status()
            id_list: list[str] = (
                search_resp.json()
                .get("esearchresult", {})
                .get("idlist", [])
            )

            if not id_list:
                logger.info("PubMed returned 0 results for '%s'", query)
                return []

            # Step 2 — efetch: retrieve article metadata as XML
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "rettype": "xml",
                "retmode": "xml",
            }
            fetch_resp = await client.get(
                f"{PUBMED_BASE_URL}efetch.fcgi", params=fetch_params
            )
            fetch_resp.raise_for_status()

        papers = self._parse_pubmed_xml(fetch_resp.text)
        logger.info("PubMed returned %d papers for '%s'", len(papers), query)
        return papers

    @staticmethod
    def _parse_pubmed_xml(xml_text: str) -> list[PaperResult]:
        """Parse PubMed efetch XML into PaperResult objects."""
        root = ElementTree.fromstring(xml_text)
        papers: list[PaperResult] = []

        for article_el in root.findall(".//PubmedArticle"):
            medline = article_el.find("MedlineCitation")
            if medline is None:
                continue

            article = medline.find("Article")
            if article is None:
                continue

            # Title
            title_el = article.find("ArticleTitle")
            title = title_el.text if title_el is not None and title_el.text else ""

            # Abstract
            abstract_parts: list[str] = []
            abstract_el = article.find("Abstract")
            if abstract_el is not None:
                for text_el in abstract_el.findall("AbstractText"):
                    if text_el.text:
                        abstract_parts.append(text_el.text)
            abstract = " ".join(abstract_parts)

            # Authors
            authors: list[str] = []
            author_list = article.find("AuthorList")
            if author_list is not None:
                for author_el in author_list.findall("Author"):
                    last = author_el.findtext("LastName", "")
                    fore = author_el.findtext("ForeName", "")
                    name = f"{fore} {last}".strip()
                    if name:
                        authors.append(name)

            # Published date
            pub_date_el = article.find(".//PubDate")
            published: str | None = None
            if pub_date_el is not None:
                year = pub_date_el.findtext("Year", "")
                month = pub_date_el.findtext("Month", "")
                day = pub_date_el.findtext("Day", "")
                date_parts = [p for p in (year, month, day) if p]
                if date_parts:
                    published = "-".join(date_parts)

            # PubMed ID -> URL
            pmid_el = medline.find("PMID")
            pmid = pmid_el.text if pmid_el is not None and pmid_el.text else ""
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""

            papers.append(
                PaperResult(
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    url=url,
                    source="pubmed",
                    published=published,
                )
            )

        return papers

    # ------------------------------------------------------------------
    # Unified search dispatcher
    # ------------------------------------------------------------------

    async def search(
        self,
        query: str,
        sources: list[str] | None = None,
        max_results: int | None = None,
    ) -> list[PaperResult]:
        """Search one or more sources in parallel and merge results.

        Args:
            query: The search query string.
            sources: List of source names (``"arxiv"``, ``"pubmed"``).
                     Defaults to both.
            max_results: Per-source cap. Falls back to ``settings.max_papers``.
        """
        sources = sources or ["arxiv", "pubmed"]
        max_results = max_results or settings.max_papers

        tasks: list[asyncio.Task[list[PaperResult]]] = []

        if "arxiv" in sources:
            tasks.append(
                asyncio.create_task(self.search_arxiv(query, max_results))
            )
        if "pubmed" in sources:
            tasks.append(
                asyncio.create_task(self.search_pubmed(query, max_results))
            )

        if not tasks:
            logger.warning("No valid sources in %s — returning empty", sources)
            return []

        results = await asyncio.gather(*tasks, return_exceptions=True)

        papers: list[PaperResult] = []
        for result in results:
            if isinstance(result, BaseException):
                logger.error("Paper fetch failed: %s", result)
                continue
            papers.extend(result)

        logger.info(
            "Combined search returned %d papers from %s", len(papers), sources
        )
        return papers
