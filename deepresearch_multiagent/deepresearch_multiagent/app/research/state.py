from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Source:
    title: str
    url: str
    snippet: str
    source: str = "web"
    score: float = 0.0


@dataclass
class Evidence:
    claim: str
    support: str
    source_url: str
    confidence: Literal["low", "medium", "high"] = "medium"


@dataclass
class ResearchState:
    topic: str
    depth: Literal["quick", "standard", "deep"] = "standard"
    language: Literal["zh", "en"] = "zh"
    session_id: str = field(default_factory=lambda: uuid4().hex)
    status: Literal["created", "running", "completed", "failed"] = "created"
    current_agent: Optional[str] = None

    plan: List[str] = field(default_factory=list)
    questions: List[str] = field(default_factory=list)
    queries: List[str] = field(default_factory=list)
    sources: List[Source] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    analysis: Dict[str, Any] = field(default_factory=dict)
    critique: Dict[str, Any] = field(default_factory=dict)
    final_report: Optional[str] = None
    errors: List[str] = field(default_factory=list)

    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    def touch(self) -> None:
        self.updated_at = now_iso()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchState":
        data = dict(data)
        data["sources"] = [Source(**x) if isinstance(x, dict) else x for x in data.get("sources", [])]
        data["evidence"] = [Evidence(**x) if isinstance(x, dict) else x for x in data.get("evidence", [])]
        return cls(**data)
