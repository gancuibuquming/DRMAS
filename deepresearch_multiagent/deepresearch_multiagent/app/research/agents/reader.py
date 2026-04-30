import json
from typing import AsyncIterator

from app.core.events import ResearchEvent
from app.research.agents.base import BaseAgent
from app.research.state import Evidence, ResearchState
from app.tools.web_reader import fetch_text


class ReaderAgent(BaseAgent):
    name = "reader"
    display_name = "Reader Agent"

    async def run(self, state: ResearchState) -> AsyncIterator[ResearchEvent]:
        if not state.sources:
            yield self.event(state, "没有可阅读的来源，跳过证据抽取。")
            return

        max_sources = 4 if state.depth == "quick" else 8 if state.depth == "standard" else 12
        selected = state.sources[:max_sources]
        yield self.event(state, f"开始阅读并抽取证据，来源数：{len(selected)}。")

        evidence = list(state.evidence)
        for src in selected:
            raw_text = await fetch_text(src.url)
            context = raw_text[:6000] if raw_text else src.snippet
            system = """
You are an evidence reader / 证据阅读 Agent.
Extract useful evidence from the given source for the research topic.
Return JSON only with keys: claims, notes.
claims is a list of objects with keys: claim, support, source_url, confidence.
Confidence must be low, medium, or high.
""".strip()
            user = json.dumps(
                {
                    "topic": state.topic,
                    "source": src.__dict__,
                    "content": context,
                    "language": state.language,
                },
                ensure_ascii=False,
            )
            try:
                result = await self.llm.complete_json(system, user, temperature=0.1)
                for item in result.get("claims", []):
                    evidence.append(
                        Evidence(
                            claim=str(item.get("claim", "")).strip(),
                            support=str(item.get("support", "")).strip(),
                            source_url=str(item.get("source_url") or src.url),
                            confidence=item.get("confidence", "medium")
                            if item.get("confidence") in {"low", "medium", "high"}
                            else "medium",
                        )
                    )
                yield self.event(state, f"已抽取来源证据：{src.title}", source=src.__dict__)
            except Exception as exc:
                state.errors.append(f"Reader failed on {src.url}: {exc}")
                yield self.event(state, f"来源阅读失败，已跳过：{src.title}", error=str(exc), source=src.__dict__)

        state.evidence = [e for e in evidence if e.claim]
        yield self.event(state, "证据抽取完成。", evidence_count=len(state.evidence))
