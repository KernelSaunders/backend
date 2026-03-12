from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class IssueReports(BaseModel):
    issue_id: str
    product_id: str | None = None
    reported_by: str | None = None  # Can be anonymous
    type: Literal["claim_false", "evidence_missing", "data_incorrect", "other"]
    description: str
    status: Literal["open", "under_review", "resolved", "rejected"] = "open"
    resolution_note: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class ChangeLog(BaseModel):
    log_id: str
    entity_type: Literal[
        "product", "stage", "claim", "evidence", "input_share", "mission"
    ]
    entity_id: str
    changed_by: str | None = None
    change_summary: str | dict | None = None 
    timestamp: datetime
