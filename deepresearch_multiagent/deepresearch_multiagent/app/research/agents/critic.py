import json
from typing import AsyncIterator

from app.core.events import ResearchEvent
from app.research.agents.base import BaseAgent
from app.research.state import ResearchState


class CriticAgent(BaseAgent):
    name = "critic"
    display_name = "Critic Agent"

    async def run(self, state: ResearchState) -> AsyncIterator[ResearchEvent]:
        yield self.event(state, "开始可信度审查，检查证据覆盖、幻觉风险与引用风险。")

        system = """
You are a strict research critic / 可信度审查 Agent.
Audit the current research state for hallucination risk, weak evidence, missing citations, and unsupported claims.
Return JSON only with keys: risk_level, issues, recommendations, pass.
- risk_level: low, medium, or high
- issues: list
- recommendations: list
- pass: boolean
""".strip()
        user = json.dumps(
            {
                "topic": state.topic,
                "questions": state.questions,
                "evidence": [e.__dict__ for e in state.evidence],
                "analysis": state.analysis,
                "source_count": len(state.sources),
                "language": state.language,
            },
            ensure_ascii=False,
        )
        state.critique = await self.llm.complete_json(system, user, temperature=0.1)
        yield self.event(state, "可信度审查完成。", critique=state.critique)
