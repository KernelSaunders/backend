from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field


class Product(BaseModel):
    product_id: str
    name: str
    category: Literal["food", "luxury", "supplements", "other"]
    brand: str | None = None
    description: str | None = None
    image: str | None = None
    created_at: datetime
    updated_at: datetime


class Stage(BaseModel):
    stage_id: str
    product_id: str | None = None
    stage_type: str
    location_country: str | None = None
    location_region: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None
    sequence_order: int | None = None
    created_at: datetime | None = None


class InputShare(BaseModel):
    input_id: str
    product_id: str | None = None
    input_name: str
    country: str
    percentage: Decimal | None = None
    notes: str | None = None
    created_at: datetime


class Claim(BaseModel):
    claim_id: str
    product_id: str | None = None
    claim_type: str
    claim_text: str
    confidence_label: Literal["verified", "partially_verified", "unverified"]
    rationale: str | None = None
    created_at: datetime
    updated_at: datetime


class Evidence(BaseModel):
    evidence_id: str
    stage_id: str | None = None
    claim_id: str | None = None
    type: str
    issuer: str
    evidence_date: date | None = Field(default=None, alias="date")
    summary: str | None = None
    file_reference: str | None = None
    created_at: datetime


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

