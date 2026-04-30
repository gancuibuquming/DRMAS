import json
from typing import AsyncIterator

from app.core.events import ResearchEvent
from app.research.agents.base import BaseAgent
from app.research.state import ResearchState


class WriterAgent(BaseAgent):
    name = "writer"
    display_name = "Writer Agent"

    async def run(self, state: ResearchState) -> AsyncIterator[ResearchEvent]:
        yield self.event(state, "开始生成最终研究报告。")

        system = """
You are a research writer / 报告撰写 Agent.
Write a clear, structured DeepResearch report.
Important rules:
1. Distinguish facts, synthesis, inference, and recommendations.
2. Do not invent sources. Use only the provided source URLs.
3. Include a Sources section at the end.
4. If evidence is weak or mock, explicitly state the limitation.
5. Write in the requested language.
""".strip()
        user = json.dumps(
            {
                "topic": state.topic,
                "depth": state.depth,
                "language": state.language,
                "plan": state.plan,
                "questions": state.questions,
                "sources": [s.__dict__ for s in state.sources],
                "evidence": [e.__dict__ for e in state.evidence],
                "analysis": state.analysis,
                "critique": state.critique,
            },
            ensure_ascii=False,
        )
        report = await self.llm.complete(system, user, temperature=0.25)
        state.final_report = report.strip()
        yield self.event(state, "最终研究报告已生成。", final_report=state.final_report)
