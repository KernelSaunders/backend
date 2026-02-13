from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class Claim(BaseModel):
    claim_id: str
    product_id: str | None = None
    claim_type: str
    claim_text: str
    confidence_label: Literal["verified", "partially_verified", "unverified"]
    rationale: str | None = None
    verified_by: str | None = None 
    verified_at: datetime | None = None  
    verification_notes: str | None = None  
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

class VerifyClaimRequest(BaseModel):
    notes: str | None = None
    
class UpdateConfidenceRequest(BaseModel):
    confidence_label: str 
    notes: str | None = None