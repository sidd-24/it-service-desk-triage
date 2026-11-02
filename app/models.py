from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.config import CATEGORIES

Category = Literal[tuple(CATEGORIES)]
Level = Literal["high", "medium", "low"]
Priority = Literal["P1", "P2", "P3", "P4", "P5"]


class TicketIn(BaseModel):
    subject: str = Field(min_length=1, max_length=300)
    description: str = Field(min_length=1, max_length=10_000)
    created_at: datetime | None = Field(None, description="Defaults to now (UTC)")


class LLMTriage(BaseModel):
    """What the LLM must return. Anything else fails validation."""
    category: Category
    impact: Level
    urgency: Level
    affected_service: str = Field(max_length=100)
    summary: str = Field(max_length=300)
    language: str = Field(max_length=5)
    confidence: float = Field(ge=0, le=1)
    rationale: str = Field(max_length=400)
    draft_reply: str = Field(max_length=1500)


class TriageResult(BaseModel):
    category: Category
    impact: Level
    urgency: Level
    priority: Priority
    resolver_group: str
    affected_service: str
    summary: str
    language: str
    confidence: float
    rationale: str
    draft_reply: str
    first_response_due: datetime
    resolution_due: datetime
    needs_human_review: bool
    review_reasons: list[str]
    source: Literal["llm", "keyword_fallback"]
