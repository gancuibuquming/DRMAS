import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ResearchEvent:
    """Standard event for SSE and CLI streaming."""

    type: str
    session_id: str
    agent: Optional[str] = None
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)

    def to_sse(self) -> str:
        payload = json.dumps(asdict(self), ensure_ascii=False)
        return f"event: {self.type}\ndata: {payload}\n\n"
