import pytest

from app.research.graph import ResearchGraph
from app.research.state import ResearchState


@pytest.mark.asyncio
async def test_graph_runs_with_mock_clients(tmp_path, monkeypatch):
    monkeypatch.setenv("CHECKPOINT_DIR", str(tmp_path))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)

    state = ResearchState(topic="test topic", depth="quick", language="zh")
    graph = ResearchGraph()
    events = []
    async for event in graph.run(state):
        events.append(event.type)

    assert state.status == "completed"
    assert state.final_report
    assert "session_completed" in events
