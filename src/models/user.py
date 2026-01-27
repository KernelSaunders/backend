from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel


class QuestMission(BaseModel):
    mission_id: str
    product_id: str | None = None
    tier: Literal["basic", "intermediate", "advanced"]
    question: str
    answer_key: dict[str, Any] | None = None
    grading_type: Literal["auto", "manual"]
    explanation_link: str | None = None
    created_at: datetime


class UserProgress(BaseModel):
    user_id: str
    mission_id: str
    completed: bool = False
    score: int | None = None
    attempts: int | None = None
    completed_at: datetime | None = None
    created_at: datetime


class UserRole(BaseModel):
    role_id: str
    user_id: str | None = None
    role: Literal["consumer", "verifier", "maintainer"] | None = None
    created_at: datetime

