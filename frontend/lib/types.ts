export interface PaperResult {
  title: string
  authors: string[]
  abstract: string
  url: string
  source: "arxiv" | "pubmed"
  published: string | null
  relevance_score: number | null
}

export interface AgentStep {
  node: string
  status: "running" | "completed" | "skipped"
  detail: string
  duration_ms: number | null
}

export interface Citation {
  index: number
  title: string
  url: string
}

export interface SearchResponse {
  query: string
  answer: string
  citations: Citation[]
  papers: PaperResult[]
  steps: AgentStep[]
  rewrite_count: number
}

export interface SearchRequest {
  query: string
  sources: string[]
  max_results: number
}
