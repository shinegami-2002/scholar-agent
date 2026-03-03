"""Synthesizer node — formats the final response and cleans up citations."""

import logging
import re
import time

from app.agents.state import AgentState

logger = logging.getLogger(__name__)


def synthesize_response(state: AgentState) -> AgentState:
    """Clean up the answer, ensure citation indices are consistent, and finalize."""
    start = time.perf_counter()

    answer = state.get("answer", "")
    citations = list(state.get("citations", []))

    # --- Remove citation references that don't have a matching citation entry ---
    valid_indices = {c["index"] for c in citations}
    if valid_indices:
        # Find all [N] references in the answer
        referenced = {int(m) for m in re.findall(r"\[(\d+)\]", answer)}
        # Remove citations that are never referenced
        citations = [c for c in citations if c["index"] in referenced]

        # Remove dangling references from the answer (cited but no entry)
        for idx in referenced - valid_indices:
            answer = answer.replace(f"[{idx}]", "")

    # --- Clean up extra whitespace from removed references ---
    answer = re.sub(r"  +", " ", answer).strip()

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    logger.info("Response synthesized in %dms", elapsed_ms)

    steps = list(state.get("steps", []))
    steps.append({
        "node": "synthesizer",
        "status": "completed",
        "detail": f"Final answer: {len(answer)} chars, {len(citations)} citations",
        "duration_ms": elapsed_ms,
    })

    return {**state, "answer": answer, "citations": citations, "steps": steps}
