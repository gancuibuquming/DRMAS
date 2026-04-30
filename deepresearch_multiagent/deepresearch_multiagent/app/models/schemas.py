from typing import Literal, Optional

from pydantic import BaseModel, Field


class CreateResearchSessionRequest(BaseModel):
    topic: str = Field(..., min_length=2, description="Research topic or question")
    depth: Literal["quick", "standard", "deep"] = "standard"
    language: Literal["zh", "en"] = "zh"


class CreateResearchSessionResponse(BaseModel):
    session_id: str
    stream_url: str


class ResearchSessionResponse(BaseModel):
    session_id: str
    topic: str
    status: str
    current_agent: Optional[str] = None
    final_report: Optional[str] = None
