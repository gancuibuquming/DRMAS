import json
from typing import AsyncIterator

from app.core.events import ResearchEvent
from app.research.agents.base import BaseAgent
from app.research.state import ResearchState


class AnalystAgent(BaseAgent):
    name = "analyst"
    display_name = "Analyst Agent"

    async def run(self, state: ResearchState) -> AsyncIterator[ResearchEvent]:
        yield self.event(state, "开始综合分析证据，归纳主题、冲突与缺口。")

        system = """
You are a research analyst / 综合分析 Agent.
Synthesize evidence into structured findings.
Return JSON only with keys: themes, synthesis, conflicts, gaps.
- themes: list of key themes
- synthesis: concise integrated analysis
- conflicts: list of conflicting or uncertain points
- gaps: list of missing evidence or next research needs
""".strip()
        user = json.dumps(
            {
                "topic": state.topic,
                "questions": state.questions,
                "sources": [s.__dict__ for s in state.sources],
                "evidence": [e.__dict__ for e in state.evidence],
                "language": state.language,
            },
            ensure_ascii=False,
        )
        state.analysis = await self.llm.complete_json(system, user, temperature=0.2)
        yield self.event(state, "综合分析完成。", analysis=state.analysis)
