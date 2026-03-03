from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    google_api_key: str = ""

    # ChromaDB
    chroma_persist_dir: str = "./data/chroma"
    chroma_collection_name: str = "scholar_papers"

    # Embedding model
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # LLM settings (all free-tier Gemini — each model has separate 20 RPD quota)
    primary_model: str = "gemini-2.5-flash"
    fallback_model: str = "gemini-2.0-flash"
    tertiary_model: str = "gemini-2.0-flash-lite"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2048

    # Paper search
    max_papers: int = 15
    top_k_results: int = 5

    # Agent
    max_rewrite_retries: int = 2
    hallucination_threshold: float = 0.3

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
