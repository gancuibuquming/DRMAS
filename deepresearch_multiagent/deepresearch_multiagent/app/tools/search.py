from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

import httpx

from app.core.config import get_settings
from app.research.state import Source


class SearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str, *, max_results: int = 5) -> List[Source]:
        raise NotImplementedError


class MockSearchProvider(SearchProvider):
    async def search(self, query: str, *, max_results: int = 5) -> List[Source]:
        return [
            Source(
                title=f"Mock Source {idx + 1}: {query}",
                url=f"mock://source/{idx + 1}?q={query}",
                snippet=(
                    f"这是关于『{query}』的模拟检索片段，用于本地跑通 DeepResearch 多 Agent 流程。"
                    "接入真实搜索 API 后，这里会替换为真实网页标题、链接和摘要。"
                ),
                source="mock",
                score=1.0 - idx * 0.1,
            )
            for idx in range(max_results)
        ]


class TavilySearchProvider(SearchProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.tavily_api_key
        self.timeout = settings.search_timeout_seconds
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY is missing")

    async def search(self, query: str, *, max_results: int = 5) -> List[Source]:
        payload: Dict[str, Any] = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": max_results,
            "include_answer": False,
            "include_raw_content": False,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post("https://api.tavily.com/search", json=payload)
            response.raise_for_status()
            data = response.json()

        results = []
        for item in data.get("results", []):
            results.append(
                Source(
                    title=item.get("title") or "Untitled",
                    url=item.get("url") or "",
                    snippet=item.get("content") or "",
                    source="tavily",
                    score=float(item.get("score") or 0.0),
                )
            )
        return results


class SerpAPISearchProvider(SearchProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.serpapi_api_key
        self.timeout = settings.search_timeout_seconds
        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY is missing")

    async def search(self, query: str, *, max_results: int = 5) -> List[Source]:
        params = {"engine": "google", "q": query, "api_key": self.api_key, "num": max_results}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get("https://serpapi.com/search.json", params=params)
            response.raise_for_status()
            data = response.json()

        results = []
        for item in data.get("organic_results", [])[:max_results]:
            results.append(
                Source(
                    title=item.get("title") or "Untitled",
                    url=item.get("link") or "",
                    snippet=item.get("snippet") or "",
                    source="serpapi",
                    score=0.0,
                )
            )
        return results


def get_search_provider() -> SearchProvider:
    settings = get_settings()
    if settings.tavily_api_key:
        return TavilySearchProvider()
    if settings.serpapi_api_key:
        return SerpAPISearchProvider()
    return MockSearchProvider()
