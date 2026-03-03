import json
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.models.schemas import SearchRequest, SearchResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ScholarAgent API starting up")
    yield
    logger.info("ScholarAgent API shutting down")


app = FastAPI(
    title="ScholarAgent API",
    description="Agentic RAG research assistant with LangGraph",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "scholar-agent"}


@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Run the agent graph and return the full search response."""
    from app.agents.graph import run_search

    start = time.time()
    try:
        response = await run_search(
            query=request.query,
            sources=request.sources,
            max_results=request.max_results,
        )
    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            logger.warning("Rate limited during search: %s", err_str[:200])
            return JSONResponse(
                status_code=429,
                content={"detail": "Gemini API rate limit reached. Please wait a moment and try again."},
            )
        logger.error("Search failed: %s", err_str[:300])
        return JSONResponse(
            status_code=500,
            content={"detail": f"Search failed: {err_str[:200]}"},
        )
    elapsed_ms = int((time.time() - start) * 1000)
    logger.info(f"Search completed in {elapsed_ms}ms for query: {request.query[:80]}")
    return response


@app.websocket("/ws/search")
async def websocket_search(websocket: WebSocket):
    """Stream agent steps in real-time via WebSocket."""
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        request = SearchRequest.model_validate_json(data)

        from app.agents.graph import build_graph
        from app.agents.state import AgentState

        graph = build_graph()
        initial_state: AgentState = {
            "query": request.query,
            "documents": [],
            "graded_documents": [],
            "rewrite_count": 0,
            "answer": "",
            "hallucination_score": 0.0,
            "steps": [],
            "citations": [],
            "sources": request.sources,
            "max_results": request.max_results,
        }

        prev_steps_count = 0
        final_state = dict(initial_state)
        async for state_update in graph.astream(initial_state):
            for node_name, node_state in state_update.items():
                final_state.update(node_state)
                steps = node_state.get("steps", [])
                if len(steps) > prev_steps_count:
                    new_steps = steps[prev_steps_count:]
                    for step in new_steps:
                        await websocket.send_text(
                            json.dumps({"type": "step", "data": step})
                        )
                    prev_steps_count = len(steps)

        from app.models.schemas import AgentStep, Citation, PaperResult

        response = SearchResponse(
            query=request.query,
            answer=final_state.get("answer", ""),
            citations=[Citation(**c) for c in final_state.get("citations", [])],
            papers=[PaperResult(**p) for p in final_state.get("graded_documents", [])],
            steps=[AgentStep(**s) for s in final_state.get("steps", [])],
            rewrite_count=final_state.get("rewrite_count", 0),
        )
        await websocket.send_text(
            json.dumps({"type": "result", "data": response.model_dump()})
        )
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_text(
                json.dumps({"type": "error", "data": str(e)})
            )
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
