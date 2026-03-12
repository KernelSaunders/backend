import uuid
from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel

from ..models import IssueReport
from ..database import select_by_id, get_client, insert_one, update_by_id, log_entity_change
from ..auth import get_current_user_id, require_verifier

router = APIRouter(prefix="/issues", tags=["issues"])

class IssueCreate(BaseModel):
    product_id: str
    type: Literal["claim_false", "evidence_missing", "data_incorrect", "other"]
    description: str


class IssueUpdate(BaseModel):
    status: Literal["open", "in_review", "resolved", "dismissed"]
    resolution_note: str | None = None


async def get_optional_user_id(
    authorization: Optional[str] = Header(default=None),
) -> str | None:
    """Return user_id if a valid Bearer token is provided, else None."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ")
    from ..database import get_client as _gc

    client = _gc()
    try:
        user_response = client.auth.get_user(token)
        user = user_response.user
        return user.id if user else None
    except Exception:
        return None


@router.post("", status_code=201)
async def create_issue(
    body: IssueCreate,
    user_id: str | None = Depends(get_optional_user_id),
):
    """
    Submit an issue report. No auth required (supports anonymous),
    but captures user_id if a valid token is provided.
    """
    issue_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    record = {
        "issue_id": issue_id,
        "product_id": body.product_id,
        "type": body.type,
        "description": body.description,
        "status": "open",
        "created_at": now,
        "updated_at": now,
    }
    if user_id:
        record["reported_by"] = user_id

    row = insert_one("IssueReports", record)
    return row


@router.get("")
async def list_issues(
    status: str | None = None,
    product_id: str | None = None,
    user_id: str = Depends(get_current_user_id),
    _verifier=Depends(require_verifier),
):
    """
    List all issue reports. Requires verifier role.
    Supports optional filters: status, product_id.
    """
    client = get_client()
    query = client.table("IssueReports").select("*")
    if status:
        query = query.eq("status", status)
    if product_id:
        query = query.eq("product_id", product_id)
    response = query.order("created_at", desc=True).execute()
    return response.data


@router.put("/{issue_id}")
async def update_issue(
    issue_id: str,
    body: IssueUpdate,
    user_id: str = Depends(get_current_user_id),
    _verifier=Depends(require_verifier),
):
    """Update issue status. Requires verifier role."""
    current = select_by_id(IssueReport, "issue_id", issue_id)
    if not current:
        raise HTTPException(status_code=404, detail="Issue not found")

    updates = {"status": body.status, "updated_at": datetime.now().isoformat()}
    if body.resolution_note is not None:
        updates["resolution_note"] = body.resolution_note

    row = update_by_id("IssueReports", "issue_id", issue_id, updates)
    log_entity_change(
        "issue",
        issue_id,
        user_id,
        {"action": "status_updated", "old_status": current.status, "new_status": body.status},
    )
    return row
