import asyncio
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.core.logging import setup_logging
from app.models.schemas import (
    CreateResearchSessionRequest,
    CreateResearchSessionResponse,
    ResearchSessionResponse,
)
from app.research.checkpoint import CheckpointStore
from app.research.graph import ResearchGraph
from app.research.state import ResearchState

setup_logging()

app = FastAPI(title="DeepResearch Multi-Agent System", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")

checkpoint_store = CheckpointStore()
# In-memory locks prevent running the same session twice in one process.
_session_locks: Dict[str, asyncio.Lock] = {}


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/research/sessions", response_model=CreateResearchSessionResponse)
async def create_research_session(req: CreateResearchSessionRequest):
    state = ResearchState(topic=req.topic, depth=req.depth, language=req.language)
    checkpoint_store.save(state)
    return CreateResearchSessionResponse(
        session_id=state.session_id,
        stream_url=f"/api/research/sessions/{state.session_id}/stream",
    )


@app.get("/api/research/sessions/{session_id}", response_model=ResearchSessionResponse)
async def get_research_session(session_id: str):
    try:
        state = checkpoint_store.load(session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")

    return ResearchSessionResponse(
        session_id=state.session_id,
        topic=state.topic,
        status=state.status,
        current_agent=state.current_agent,
        final_report=state.final_report,
    )


@app.get("/api/research/sessions/{session_id}/stream")
async def stream_research_session(session_id: str):
    try:
        state = checkpoint_store.load(session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")

    if state.status == "completed":
        async def completed_stream():
            from app.core.events import ResearchEvent
            yield ResearchEvent(
                type="session_completed",
                session_id=state.session_id,
                message="任务已经完成。",
                data={"final_report": state.final_report},
            ).to_sse()
        return StreamingResponse(completed_stream(), media_type="text/event-stream")

    lock = _session_locks.setdefault(session_id, asyncio.Lock())

    async def event_generator():
        if lock.locked():
            from app.core.events import ResearchEvent
            yield ResearchEvent(
                type="session_busy",
                session_id=session_id,
                message="该任务正在运行，请勿重复启动。",
            ).to_sse()
            return

        async with lock:
            graph = ResearchGraph(checkpoint_store=checkpoint_store)
            async for event in graph.run(state):
                yield event.to_sse()

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/research/sessions/{session_id}/resume")
async def resume_research_session(session_id: str):
    try:
        state = checkpoint_store.load(session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": state.session_id,
        "status": state.status,
        "current_agent": state.current_agent,
        "stream_url": f"/api/research/sessions/{state.session_id}/stream",
    }
