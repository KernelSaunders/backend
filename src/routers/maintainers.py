from typing import Any

from fastapi import APIRouter, Depends, Query

from ..auth import require_maintainer
from ..database import get_client
from ..models.user import UserRole

router = APIRouter(prefix="/maintainers", tags=["maintainers"])


def fetch_row(table_name: str, id_field: str, id_value: str) -> dict[str, Any] | None:
    client = get_client()
    response = (
        client.table(table_name).select("*").eq(id_field, id_value).limit(1).execute()
    )
    if not response.data:
        return None
    row = response.data[0]
    if not isinstance(row, dict):
        return None
    return row


def resolve_product_details(entry: dict[str, Any]):
    entity_type = str(entry.get("entity_type") or "").casefold()
    entity_id = entry.get("entity_id")
    change_summary = entry.get("change_summary")

    if not isinstance(entity_id, str):
        return None

    product_id = None

    if entity_type == "product":
        product_id = entity_id
    elif entity_type == "stage":
        stage = fetch_row("Stage", "stage_id", entity_id)
        if stage:
            product_id = stage.get("product_id")
    elif entity_type == "claim":
        claim = fetch_row("Claim", "claim_id", entity_id)
        if claim:
            product_id = claim.get("product_id")
    elif entity_type == "issue":
        issue = fetch_row("IssueReports", "issue_id", entity_id)
        if issue:
            product_id = issue.get("product_id")
    elif entity_type == "input_share":
        input_share = fetch_row("InputShare", "input_id", entity_id)
        if input_share:
            product_id = input_share.get("product_id")
    elif entity_type == "evidence":
        # Evidence can be linked through either a claim or a stage.
        claim_id = None
        if isinstance(change_summary, dict):
            claim_id = change_summary.get("claim_id")

        if isinstance(claim_id, str):
            claim = fetch_row("Claim", "claim_id", claim_id)
            if claim:
                product_id = claim.get("product_id")
        else:
            evidence = fetch_row("Evidence", "evidence_id", entity_id)
            if evidence:
                claim_id = evidence.get("claim_id")
                stage_id = evidence.get("stage_id")

                if isinstance(claim_id, str):
                    claim = fetch_row("Claim", "claim_id", claim_id)
                    if claim:
                        product_id = claim.get("product_id")
                elif isinstance(stage_id, str):
                    stage = fetch_row("Stage", "stage_id", stage_id)
                    if stage:
                        product_id = stage.get("product_id")

    if not isinstance(product_id, str):
        return None

    product = fetch_row("Product", "product_id", product_id)
    if not product:
        return None

    return {
        "product_id": product_id,
        "product_name": product.get("name") or product_id,
        "product_link": f"/dashboard/products/{product_id}/edit",
    }


# get audit logs (maintainers only)
@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    _maintainer: UserRole = Depends(require_maintainer),
):
    client = get_client()
    response = (
        client.table("ChangeLog")
        .select("*")
        .order("timestamp", desc=True)
        .limit(limit)
        .execute()
    )

    logs = []
    for entry in response.data or []:
        if not isinstance(entry, dict):
            continue

        product = resolve_product_details(entry)
        logs.append(
            {
                **entry,
                "product": product,
            }
        )

    return logs
