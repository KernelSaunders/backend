from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..models import Claim, Evidence, InputShare, Product, QuestMission, Stage, UserRole
from ..database import select_all, select_by_id, select_by_field, get_client, log_claim_change

from ..auth import get_current_user_id, get_current_user_role, require_verifier

def validate_uuid(value: str, field_name: str = "id") -> str:
    """Validate that a string is a valid UUID format."""
    try:
        UUID(value)
        return value
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name} format")


router = APIRouter(prefix="/products", tags=["products"])


class ClaimWithEvidence(BaseModel):
    claim: Claim
    evidence: list[Evidence]


class ProductTraceability(BaseModel):
    product: Product
    stages: list[Stage]
    input_shares: list[InputShare]
    claims: list[ClaimWithEvidence]


class ClaimEvidenceGroup(BaseModel):
    claim_id: str
    claim_type: str
    claim_text: str
    confidence_label: str
    evidence: list[Evidence]


class ProductEvidenceView(BaseModel):
    product_id: str
    groups: list[ClaimEvidenceGroup]


class QuestMissionPublic(BaseModel):
    mission_id: str
    product_id: str
    tier: Literal["basic", "intermediate", "advanced"]
    question: str
    type: Literal["multiple_choice"] = "multiple_choice"
    options: list[str]
    explanation_link: str | None = None
    created_at: datetime


@router.get("")
def get_products() -> list[Product]:
    return select_all(Product)

# Moved up here as causing bugs with route below
@router.get("/claims/pending")
async def get_pending_claims(
    user_id: str = Depends(get_current_user_id),
    _verifier: UserRole = Depends(require_verifier),
):
    """
    Get all claims that haven't been verified yet.
    Requirments: verifier role
    """
    client = get_client()
    response = (
        client.table("Claim")
        .select("*")
        .is_("verified_by", "null")
        .execute()
    )
    
    return response.data

@router.get("/{product_id}")
def get_product(product_id: str) -> Product:
    validate_uuid(product_id, "product_id")
    product = select_by_id(Product, "product_id", product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/{product_id}/traceability")
def get_product_traceability(product_id: str) -> ProductTraceability:
    validate_uuid(product_id, "product_id")
    product = select_by_id(Product, "product_id", product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    stages = select_by_field(Stage, "product_id", product_id)
    stages.sort(key=lambda s: s.sequence_order or 0)

    input_shares = select_by_field(InputShare, "product_id", product_id)

    claims = select_by_field(Claim, "product_id", product_id)
    claims_with_evidence = []

    # Consider making this async
    for claim in claims:
        evidence = select_by_field(Evidence, "claim_id", claim.claim_id)
        claims_with_evidence.append(ClaimWithEvidence(claim=claim, evidence=evidence))

    return ProductTraceability(
        product=product,
        stages=stages,
        input_shares=input_shares,
        claims=claims_with_evidence,
    )


@router.get("/{product_id}/evidence")
def get_product_evidence(product_id: str) -> ProductEvidenceView:
    """
    Returns evidence grouped by claim, shaped for the evidence view.
    Only includes claims that have at least one evidence item.
    """
    validate_uuid(product_id, "product_id")
    product = select_by_id(Product, "product_id", product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    claims = select_by_field(Claim, "product_id", product_id)
    groups: list[ClaimEvidenceGroup] = []
    for claim in claims:
        evidence = select_by_field(Evidence, "claim_id", claim.claim_id)
        if evidence:
            groups.append(ClaimEvidenceGroup(
                claim_id=claim.claim_id,
                claim_type=claim.claim_type,
                claim_text=claim.claim_text,
                confidence_label=claim.confidence_label,
                evidence=evidence,
            ))

    return ProductEvidenceView(product_id=product_id, groups=groups)


@router.get("/{product_id}/missions", response_model=list[QuestMissionPublic])
def get_product_missions(product_id: str) -> list[QuestMissionPublic]:
    validate_uuid(product_id, "product_id")
    product = select_by_id(Product, "product_id", product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    missions = select_by_field(QuestMission, "product_id", product_id)
    public: list[QuestMissionPublic] = []
    for m in missions:
        answer_key = m.answer_key or {}
        options = answer_key.get("options")

        # Don't support manual answers for now
        if m.grading_type != "auto":
            continue

        if not isinstance(options, list) or not all(isinstance(o, str) for o in options):
            raise HTTPException(
                status_code=500,
                detail=f"QuestMission {m.mission_id} has invalid answer_key.options",
            )

        public.append(
            QuestMissionPublic(
                mission_id=m.mission_id,
                product_id=m.product_id or product_id,
                tier=m.tier,
                question=m.question,
                options=options,
                explanation_link=m.explanation_link,
                created_at=m.created_at,
            )
        )
    return public

@router.put("/{product_id}/claims/{claim_id}/verify")
async def verify_claim(
    product_id: str,
    claim_id: str,
    notes: str | None = None,
    user_id: str = Depends(get_current_user_id),
    _verifier: UserRole = Depends(require_verifier),
):
    """
    Function which verifies a claim
    Requirements: Must be a verifier
    Implementation:
        1. Fetches current claim
        2. Updates claim with new info
        3. Records change in ChangeLog table
    """
    # Ensure correct form
    validate_uuid(product_id)
    validate_uuid(claim_id)
    
    # Fetch current state
    current_claim = select_by_id(Claim, "claim_id", claim_id)
    if not current_claim:
        raise HTTPException(status_code=404, detail="No such claim")

    # Creates connect with db
    # Updates the claim
    client = get_client()
    client.table("Claim").update({
        "verified_by": user_id,
        "verified_at": datetime.now().isoformat(),
        "verification_notes": notes,
        "confidence_label": "verified"
    }).eq("claim_id", claim_id).execute()
    
    # Log the change
    log_claim_change(
        claim_id=claim_id,
        changed_by=user_id,
        action="verified",
        old_confidence=current_claim.confidence_label,
        new_confidence="verified",
        notes=notes,
        old_verified=False,
        new_verified=True,
    )
    
    return {"status": "verified"}

@router.put("/{product_id}/claims/{claim_id}/unverify")
async def unverify_claim(
    product_id: str,
    claim_id: str,
    notes: str | None = None,
    user_id: str = Depends(get_current_user_id),
    _verifier: UserRole = Depends(require_verifier),
):
    """
    Remove verification from a claim.
    Requirements: Verifier role
    """
     # Ensure correct form
    validate_uuid(product_id)
    validate_uuid(claim_id)
    
    # Fetch current state
    current_claim = select_by_id(Claim, "claim_id", claim_id)
    if not current_claim:
        raise HTTPException(status_code=404, detail="No such claim")

    # Creates connect with db
    # Updates the claim
    client = get_client()
    client.table("Claim").update({
        "verified_by": None,
        "verified_at": None,
        "verification_notes": notes, #keep for logs
        "confidence_label": "unverified"
    }).eq("claim_id", claim_id).execute()
    
    log_claim_change(
        claim_id=claim_id,
        changed_by=user_id,
        action="unverified",
        old_confidence=current_claim.confidence_label,
        new_confidence="unverified",
        notes=notes,
        old_verified=True,
        new_verified=False,
    )
    
    return {"status": "unverified"}

@router.put("/{product_id}/claims/{claim_id}/confidence")
async def update_claim_confidence(
    product_id: str,
    claim_id: str,
    confidence_label: str,  # "verified", "likely", "uncertain", "disputed"
    notes: str | None = None,
    user_id: str = Depends(get_current_user_id),
    _verifier: UserRole = Depends(require_verifier),
):
    """
    Update the confidence level of a claim.
    Requirmenents: Verifier role
    """
    # Ensure correct form
    validate_uuid(product_id)
    validate_uuid(claim_id)
    
    # Fetch current state
    current_claim = select_by_id(Claim, "claim_id", claim_id)
    if not current_claim:
        raise HTTPException(status_code=404, detail="No such claim")

    # Creates connect with db
    # Updates the claim
    client = get_client()
    client.table("Claim").update({
        "confidence_label": confidence_label
    }).eq("claim_id", claim_id).execute()

    log_claim_change(
        claim_id=claim_id,
        changed_by=user_id,
        action="confidence_updated",
        old_confidence=current_claim.confidence_label,
        new_confidence=confidence_label,
        notes=notes,
        old_verified=current_claim.verified_by is not None, 
        new_verified=current_claim.verified_by is not None,
    )
    
    return {"status": "updated"}

@router.get("/{product_id}/claims/{claim_id}/history")
async def get_verification_history(
    product_id: str,
    claim_id: str,
    user_id: str = Depends(get_current_user_id),
    _verifier: UserRole = Depends(require_verifier)
):
    """
    Get verification history from the ChangeLog table
    Requiremnts: verifier role
    """
    validate_uuid(product_id, "product_id")
    validate_uuid(claim_id, "claim_id")
    
    client = get_client()
    response = (
        client.table("ChangeLog")
        .select("*")
        .eq("entity_type", "Claim")
        .eq("entity_id", claim_id)
        .order("timestamp", desc=True)
        .execute()
    )

    return response.data

