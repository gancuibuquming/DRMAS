from typing import AsyncIterator, Dict

from app.core.config import get_settings
from app.core.events import ResearchEvent
from app.research.agents.base import BaseAgent
from app.research.state import ResearchState, Source
from app.tools.search import get_search_provider


class SearchAgent(BaseAgent):
    name = "searcher"
    display_name = "Search Agent"

    async def run(self, state: ResearchState) -> AsyncIterator[ResearchEvent]:
        settings = get_settings()
        provider = get_search_provider()

        queries = state.queries or [state.topic]
        if state.depth == "quick":
            queries = queries[:2]
        elif state.depth == "standard":
            queries = queries[:4]

        yield self.event(state, f"开始检索 {len(queries)} 个查询。", queries=queries)

        dedup: Dict[str, Source] = {s.url: s for s in state.sources}
        for query in queries:
            yield self.event(state, f"检索：{query}", query=query)
            results = await provider.search(query, max_results=settings.max_search_results)
            for item in results:
                if item.url and item.url not in dedup:
                    dedup[item.url] = item
            yield self.event(
                state,
                f"查询完成，累计来源 {len(dedup)} 条。",
                query=query,
                new_results=[r.__dict__ for r in results],
            )

        state.sources = list(dedup.values())
        yield self.event(state, "检索阶段完成。", source_count=len(state.sources))
