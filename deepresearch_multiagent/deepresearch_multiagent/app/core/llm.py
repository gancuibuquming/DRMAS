import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict

try:
    from tenacity import retry, stop_after_attempt, wait_exponential
except ImportError:
    def retry(*args, **kwargs):
        def decorator(fn):
            return fn
        return decorator

    def stop_after_attempt(*args, **kwargs):
        return None

    def wait_exponential(*args, **kwargs):
        return None

from app.core.config import get_settings


class LLMClient(ABC):
    @abstractmethod
    async def complete(self, system: str, user: str, *, temperature: float = 0.2) -> str:
        raise NotImplementedError

    async def complete_json(self, system: str, user: str, *, temperature: float = 0.1) -> Dict[str, Any]:
        text = await self.complete(system, user, temperature=temperature)
        return parse_json_object(text)


def parse_json_object(text: str) -> Dict[str, Any]:
    """Best-effort JSON extraction from LLM output."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if fence:
        return json.loads(fence.group(1))

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return json.loads(text[start : end + 1])

    raise ValueError(f"LLM did not return valid JSON: {text[:500]}")


class MockLLMClient(LLMClient):
    """Deterministic mock client for local demos and tests."""

    async def complete(self, system: str, user: str, *, temperature: float = 0.2) -> str:
        lower = (system + "\n" + user).lower()

        if "research planner" in lower or "研究规划" in lower:
            return json.dumps(
                {
                    "questions": [
                        "这个主题的核心概念和问题边界是什么？",
                        "目前主流方法或观点有哪些？",
                        "不同来源之间是否存在冲突或证据强弱差异？",
                        "落地实施时的关键风险和评估指标是什么？",
                    ],
                    "queries": [
                        "核心概念 方法 综述",
                        "最新实践 案例 指标",
                        "风险 局限性 评估 方法",
                    ],
                    "plan": [
                        "先界定主题和研究范围",
                        "检索高可信来源并抽取证据",
                        "比较不同观点并识别缺口",
                        "输出可追溯研究报告",
                    ],
                },
                ensure_ascii=False,
            )

        if "evidence reader" in lower or "证据阅读" in lower:
            return json.dumps(
                {
                    "claims": [
                        {
                            "claim": "该主题需要同时关注方法有效性、证据来源和落地约束。",
                            "support": "检索结果普遍指向方法设计、评估指标和风险控制三个维度。",
                            "source_url": "mock://source/1",
                            "confidence": "medium",
                        }
                    ],
                    "notes": "Mock 模式下仅演示证据抽取结构；接入真实搜索与 LLM 后会生成真实引用。",
                },
                ensure_ascii=False,
            )

        if "research analyst" in lower or "综合分析" in lower:
            return json.dumps(
                {
                    "themes": [
                        "问题拆解与任务规划",
                        "证据检索与信息抽取",
                        "多来源交叉验证",
                        "最终报告可追溯生成",
                    ],
                    "synthesis": "综合来看，一个可靠的 DeepResearch 系统不应只生成答案，而应保留从问题拆解、检索、阅读、分析到写作的全链路证据。",
                    "conflicts": ["Mock 模式无法验证真实网页内容，需要接入真实搜索 API。"],
                    "gaps": ["需要增加领域知识库、网页正文抓取和引用一致性检查。"],
                },
                ensure_ascii=False,
            )

        if "critic" in lower or "可信度审查" in lower:
            return json.dumps(
                {
                    "risk_level": "medium",
                    "issues": [
                        "部分结论依赖模拟来源，真实使用时需要联网检索或本地知识库支撑。",
                        "需要在最终报告中明确区分事实、推断和建议。",
                    ],
                    "recommendations": [
                        "接入 Tavily/SerpAPI 与网页正文抓取。",
                        "为每个关键结论绑定 source_url。",
                    ],
                    "pass": True,
                },
                ensure_ascii=False,
            )

        if "research writer" in lower or "报告撰写" in lower:
            return (
                "# DeepResearch 研究报告\n\n"
                "## 一、结论摘要\n\n"
                "该问题适合使用多 Agent 流程处理：先由 Planner 拆解研究问题，再由 Searcher 检索来源，Reader 抽取证据，Analyst 综合归纳，Critic 审查可信度，最后 Writer 生成可追溯报告。\n\n"
                "## 二、核心发现\n\n"
                "1. 多 Agent 的价值不在于简单串联模型，而在于把复杂研究任务拆成可检查的中间状态。\n"
                "2. SSE 可以让用户看到实时进度，降低长任务的黑盒感。\n"
                "3. Checkpoint 可以支持任务中断恢复，也便于调试每个 Agent 的输出。\n\n"
                "## 三、风险与改进\n\n"
                "当前 Mock 模式主要用于跑通流程；真实生产环境应接入搜索 API、网页正文解析、引用校验和本地知识库。\n\n"
                "## Sources\n\n"
                "- mock://source/1\n"
            )

        return "Mock response."


class OpenAILLMClient(LLMClient):
    def __init__(self) -> None:
        settings = get_settings()
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise RuntimeError("openai package is not installed") from exc

        kwargs: Dict[str, Any] = {"api_key": settings.openai_api_key, "timeout": settings.llm_timeout_seconds}
        if settings.openai_base_url:
            kwargs["base_url"] = settings.openai_base_url
        self.client = AsyncOpenAI(**kwargs)
        self.model = settings.openai_model

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3))
    async def complete(self, system: str, user: str, *, temperature: float = 0.2) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content or ""


def get_llm_client() -> LLMClient:
    settings = get_settings()
    if settings.is_mock_llm:
        return MockLLMClient()
    return OpenAILLMClient()
