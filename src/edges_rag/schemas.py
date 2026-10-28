from __future__ import annotations

from pydantic import BaseModel, Field


class Citation(BaseModel):
    path: str
    snippet: str
    score: float | None = None


class AskRequest(BaseModel):
    question: str = Field(min_length=1)


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
