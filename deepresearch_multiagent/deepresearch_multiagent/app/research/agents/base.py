from abc import ABC, abstractmethod
from typing import AsyncIterator

from app.core.events import ResearchEvent
from app.core.llm import LLMClient
from app.research.state import ResearchState


class BaseAgent(ABC):
    name: str = "base"
    display_name: str = "Base Agent"

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def event(self, state: ResearchState, message: str, **data) -> ResearchEvent:
        return ResearchEvent(
            type="agent_message",
            session_id=state.session_id,
            agent=self.name,
            message=message,
            data=data,
        )

    @abstractmethod
    async def run(self, state: ResearchState) -> AsyncIterator[ResearchEvent]:
        """Mutate state and yield progress events."""
        raise NotImplementedError
