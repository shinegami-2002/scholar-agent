"""LLM provider factory — Gemini 3 Flash primary, Gemini 2.5 Flash fallback."""

import logging
import time

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage

from app.config import settings

logger = logging.getLogger(__name__)


def extract_text(response: BaseMessage) -> str:
    """Extract text content from an LLM response, handling both str and list formats.

    Gemini 3 models return content as a list of dicts, while 2.5 returns a string.
    """
    content = response.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
        return "".join(parts)
    return str(content)


def get_llm(model_override: str | None = None) -> BaseChatModel:
    """Return a LangChain chat model using Google Gemini (free tier).

    Strategy:
      1. Use primary_model (gemini-2.5-flash) by default.
      2. model_override lets callers pick a specific model.
      3. All models use the same Google API key.
    """
    if not settings.google_api_key:
        raise RuntimeError(
            "No Google API key configured. Set GOOGLE_API_KEY in .env"
        )

    from langchain_google_genai import ChatGoogleGenerativeAI

    model = model_override or settings.primary_model
    logger.info("Using Gemini model: %s", model)
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=settings.google_api_key,
        temperature=settings.llm_temperature,
        max_output_tokens=settings.llm_max_tokens,
    )


def invoke_with_retry(
    messages: list[BaseMessage],
    model_override: str | None = None,
) -> BaseMessage:
    """Invoke an LLM with cascading fallback through 3 models on rate limits.

    Each model has its own 20 RPD free-tier quota, giving us ~60 RPD total.
    On 429: immediately try next model with a short wait.
    """
    primary = model_override or settings.primary_model
    # Cascade through 3 different models — each has separate daily quota
    model_sequence = [
        primary,
        settings.fallback_model,
        settings.tertiary_model,
        settings.tertiary_model,  # one more retry on last model
    ]

    for attempt, model in enumerate(model_sequence):
        llm = get_llm(model)
        try:
            return llm.invoke(messages)
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                wait_time = 5  # short wait, then try next model
                if "retry in" in err_str.lower():
                    import re
                    match = re.search(r"retry in (\d+\.?\d*)", err_str.lower())
                    if match:
                        wait_time = min(float(match.group(1)) + 1, 15)
                next_model = model_sequence[attempt + 1] if attempt + 1 < len(model_sequence) else "none"
                logger.warning(
                    "Rate limited on %s (attempt %d/%d), waiting %.0fs → next: %s",
                    model, attempt + 1, len(model_sequence), wait_time, next_model,
                )
                time.sleep(wait_time)
            else:
                raise

    # All models exhausted
    raise RuntimeError(
        "All Gemini models rate limited. Free tier daily quota exhausted. "
        "Try again tomorrow or set up billing at https://aistudio.google.com"
    )
