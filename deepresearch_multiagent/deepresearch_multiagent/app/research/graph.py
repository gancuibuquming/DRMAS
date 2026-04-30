import asyncio
import logging
from typing import AsyncIterator, Iterable, Optional

from app.core.events import ResearchEvent
from app.core.llm import get_llm_client
from app.research.agents.analyst import AnalystAgent
from app.research.agents.critic import CriticAgent
from app.research.agents.planner import PlannerAgent
from app.research.agents.reader import ReaderAgent
from app.research.agents.searcher import SearchAgent
from app.research.agents.writer import WriterAgent
from app.research.checkpoint import CheckpointStore
from app.research.state import ResearchState

logger = logging.getLogger(__name__)


class ResearchGraph:
    """Pure Python multi-agent graph.

    This intentionally avoids LangGraph dependency to keep the demo runnable.
    You can swap this class with LangGraph StateGraph later.
    """

    def __init__(self, checkpoint_store: Optional[CheckpointStore] = None) -> None:
        self.llm = get_llm_client()
        self.checkpoints = checkpoint_store or CheckpointStore()
        self.agents = [
            PlannerAgent(self.llm),
            SearchAgent(self.llm),
            ReaderAgent(self.llm),
            AnalystAgent(self.llm),
            CriticAgent(self.llm),
            WriterAgent(self.llm),
        ]

    def agent_names(self) -> Iterable[str]:
        return [a.name for a in self.agents]

    async def run(self, state: ResearchState, *, start_after: Optional[str] = None) -> AsyncIterator[ResearchEvent]:
        state.status = "running"
        self.checkpoints.save(state)
        yield ResearchEvent(type="session_started", session_id=state.session_id, message="研究任务已启动。")

        skip = bool(start_after)
        if not start_after:
            skip = False

        try:
            for agent in self.agents:
                if start_after and skip:
                    if agent.name == start_after:
                        skip = False
                    continue

                state.current_agent = agent.name
                self.checkpoints.save(state)
                yield ResearchEvent(
                    type="agent_started",
                    session_id=state.session_id,
                    agent=agent.name,
                    message=f"{agent.display_name} started.",
                )

                async for event in agent.run(state):
                    yield event

                self.checkpoints.save(state)
                yield ResearchEvent(
                    type="agent_finished",
                    session_id=state.session_id,
                    agent=agent.name,
                    message=f"{agent.display_name} finished.",
                )

            state.current_agent = None
            state.status = "completed"
            self.checkpoints.save(state)
            yield ResearchEvent(type="session_completed", session_id=state.session_id, message="研究任务已完成。")

        except asyncio.CancelledError:
            logger.warning("Research session cancelled: %s", state.session_id)
            self.checkpoints.save(state)
            raise
        except Exception as exc:
            logger.exception("Research session failed: %s", state.session_id)
            state.status = "failed"
            state.errors.append(str(exc))
            self.checkpoints.save(state)
            yield ResearchEvent(
                type="session_failed",
                session_id=state.session_id,
                agent=state.current_agent,
                message="研究任务失败。",
                data={"error": str(exc)},
            )
