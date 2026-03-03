from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """User search request."""

    query: str = Field(..., min_length=1, max_length=500)
    sources: list[str] = Field(default=["arxiv", "pubmed"])
    max_results: int = Field(default=10, ge=1, le=50)


class PaperResult(BaseModel):
    """A single paper from arXiv or PubMed."""

    title: str
    authors: list[str]
    abstract: str
    url: str
    source: str  # "arxiv" or "pubmed"
    published: str | None = None
    relevance_score: float | None = None


class AgentStep(BaseModel):
    """A single step in the agent execution trace."""

    node: str
    status: str  # "running", "completed", "skipped"
    detail: str = ""
    duration_ms: int | None = None


class Citation(BaseModel):
    """Inline citation linking answer text to a source paper."""

    index: int
    title: str
    url: str


class SearchResponse(BaseModel):
    """Full response from the agent pipeline."""

    query: str
    answer: str
    citations: list[Citation] = []
    papers: list[PaperResult] = []
    steps: list[AgentStep] = []
    rewrite_count: int = 0
