import json
from typing import AsyncIterator

from app.core.events import ResearchEvent
from app.research.agents.base import BaseAgent
from app.research.state import ResearchState


class PlannerAgent(BaseAgent):
    name = "planner"
    display_name = "Planner Agent"

    async def run(self, state: ResearchState) -> AsyncIterator[ResearchEvent]:
        yield self.event(state, "开始拆解研究问题，生成研究计划与检索式。")

        system = """
You are a research planner / 研究规划 Agent.
Your job is to decompose a user topic into a clear research plan.
Return JSON only with keys: questions, queries, plan.
- questions: 3-6 research questions
- queries: 3-8 search queries
- plan: 3-6 concise steps
""".strip()
        user = json.dumps(
            {"topic": state.topic, "depth": state.depth, "language": state.language},
            ensure_ascii=False,
        )
        result = await self.llm.complete_json(system, user, temperature=0.1)

        state.questions = [str(x) for x in result.get("questions", [])]
        state.queries = [str(x) for x in result.get("queries", [])]
        state.plan = [str(x) for x in result.get("plan", [])]

        yield self.event(
            state,
            "研究计划已生成。",
            questions=state.questions,
            queries=state.queries,
            plan=state.plan,
        )
