import os
import uuid
from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from ..auth import get_current_user_id, get_current_user_role, require_verifier
from ..database import (
    get_client,
    insert_one,
    log_claim_change,
    log_entity_change,
    select_all,
    select_by_field,
    select_by_id,
    update_by_id,
)
from ..models import Claim, Evidence, InputShare, Product, QuestMission, Stage, UserRole


class ProductCreate(BaseModel):
    name: str
    category: Literal["food", "luxury", "supplements", "other"]
    brand: str | None = None
    description: str | None = None
    image: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    category: Literal["food", "luxury", "supplements", "other"] | None = None
    brand: str | None = None
    description: str | None = None
    image: str | None = None


class StageCreate(BaseModel):
    stage_type: str
    location_country: str | None = None
    location_region: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None
    sequence_order: int | None = None


class StageUpdate(BaseModel):
    stage_type: str | None = None
    location_country: str | None = None
    location_region: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None
    sequence_order: int | None = None


class ClaimCreate(BaseModel):
    claim_type: str
    claim_text: str
    confidence_label: Literal["verified", "partially_verified", "unverified"] = (
        "unverified"
    )
    rationale: str | None = None


class EvidenceCreate(BaseModel):
    type: str
    issuer: str
    date: str | None = None
    summary: str | None = None
    file_reference: str | None = None
    stage_id: str | None = None


class ClaimWithEvidence(BaseModel):
    claim: Claim
    evidence: list[Evidence]


class ProductTraceability(BaseModel):
    product: Product
    stages: list[Stage]
    input_shares: list[InputShare]
    claims: list[Claim]


class StageEvidenceGroup(BaseModel):
    stage_id: str
    stage_type: str
    description: str | None = None
    evidence: list[Evidence]


class ProductStageEvidenceView(BaseModel):
    product_id: str
    groups: list[StageEvidenceGroup]


class ClaimEvidenceGroup(BaseModel):
    claim_id: str
    claim_type: str
    claim_text: str
    confidence_label: str
    rationale: str | None = None
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


def validate_uuid(value: str, field_name: str = "id") -> str:
    """Validate that a string is a valid UUID format."""
    try:
        UUID(value)
        return value
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name} format")


def normalize_filename(filename: str | None) -> str:
    cleaned = os.path.basename(filename or "evidence")
    cleaned = cleaned.replace(" ", "_")
    return cleaned or "evidence"


def validate_evidence_target(
    product_id: str, claim_id: str | None, stage_id: str | None
):
    if bool(claim_id) == bool(stage_id):
        raise HTTPException(
            status_code=400,
            detail="Provide exactly one of claim_id or stage_id",
        )

    if claim_id:
        validate_uuid(claim_id, "claim_id")
        claim = select_by_id(Claim, "claim_id", claim_id)
        if not claim or claim.product_id != product_id:
            raise HTTPException(status_code=404, detail="Claim not found")
        return {"claim": claim, "stage": None}

    validate_uuid(stage_id or "", "stage_id")
    stage = select_by_id(Stage, "stage_id", stage_id or "")
    if not stage or stage.product_id != product_id:
        raise HTTPException(status_code=404, detail="Stage not found")
    return {"claim": None, "stage": stage}


router = APIRouter(prefix="/products", tags=["products"])

# Routes registration for creating a product


@router.post("", status_code=201)
async def create_product(
    body: ProductCreate,
    user_id: str = Depends(get_current_user_id),
    _verifier: UserRole = Depends(require_verifier),
):
    """Create a new product. Requires verifier role."""
    product_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    record = {
        "product_id": product_id,
        **body.model_dump(exclude_none=True),
        "created_at": now,
        "updated_at": now,
    }
    row = insert_one("Product", record)
    log_entity_change(
        "product",
        product_id,
        user_id,
        {"action": "created", "fields": body.model_dump(exclude_none=True)},
    )
    return row


@router.put("/{product_id}")
async def update_product(
    product_id: str,
    body: ProductUpdate,
    user_id: str = Depends(get_current_user_id),
    _verifier: UserRole = Depends(require_verifier),
):
    """Update an existing product. Requires verifier role."""
    validate_uuid(product_id, "product_id")
    current = select_by_id(Product, "product_id", product_id)
    if not current:
        raise HTTPException(status_code=404, detail="Product not found")

    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates["updated_at"] = datetime.now().isoformat()

    # Build old vs new for the change log
    old_values = {}
    for field in updates:
        if field != "updated_at":
            old_values[field] = getattr(current, field)
    row = update_by_id("Product", "product_id", product_id, updates)
    log_entity_change(
        "product",
        product_id,
        user_id,
        {
            "action": "updated",
            "old": old_values,
            "new": body.model_dump(exclude_none=True),
        },
    )
    return row


@router.post("/{product_id}/stages", status_code=201)
async def create_stage(
    product_id: str,
    body: StageCreate,
    user_id: str = Depends(get_current_user_id),
    _verifier: UserRole = Depends(require_verifier),
):
    """Add a stage to a product. Requires verifier role."""
    validate_uuid(product_id, "product_id")
    product = select_by_id(Product, "product_id", product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    stage_id = str(uuid.uuid4())
    record = {
        "stage_id": stage_id,
        "product_id": product_id,
        **body.model_dump(exclude_none=True),
        "created_at": datetime.now().isoformat(),
    }
    row = insert_one("Stage", record)
    log_entity_change(
        "stage",
        stage_id,
        user_id,
        {
            "action": "created",
            "product_id": product_id,
            "fields": body.model_dump(exclude_none=True),
        },
    )
    return row


@router.put("/{product_id}/stages/{stage_id}")
async def update_stage(
    product_id: str,
    stage_id: str,
    body: StageUpdate,
    user_id: str = Depends(get_current_user_id),
    _verifier: UserRole = Depends(require_verifier),
):
    """Update a stage. Requires verifier role."""
    validate_uuid(product_id, "product_id")
    validate_uuid(stage_id, "stage_id")

    current = select_by_id(Stage, "stage_id", stage_id)
    if not current:
        raise HTTPException(status_code=404, detail="Stage not found")

    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    old_values = {}
    for field in updates:
        old_values[field] = getattr(current, field)
    row = update_by_id("Stage", "stage_id", stage_id, updates)
    log_entity_change(
        "stage",
        stage_id,
        user_id,
        {"action": "updated", "old": old_values, "new": updates},
    )
    return row


@router.post("/{product_id}/claims", status_code=201)
async def create_claim(
    product_id: str,
    body: ClaimCreate,
    user_id: str = Depends(get_current_user_id),
    _verifier: UserRole = Depends(require_verifier),
):
    """
    Add a claim to a product. Requires verifier role.
    Claims without evidence must be marked unverified with a rationale.
    """
    validate_uuid(product_id, "product_id")
    product = select_by_id(Product, "product_id", product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Integrity rule: non-unverified claims must have evidence (added later), but at
    # creation time there's no evidence yet, so the claim must be "unverified" with a rationale.
    if body.confidence_label != "unverified":
        raise HTTPException(
            status_code=400,
            detail="New claims must be marked 'unverified' — add evidence first, then verify.",
        )
    if not body.rationale:
        raise HTTPException(
            status_code=400,
            detail="Claims marked 'unverified' must include a rationale.",
        )

    claim_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    record = {
        "claim_id": claim_id,
        "product_id": product_id,
        **body.model_dump(exclude_none=True),
        "created_at": now,
        "updated_at": now,
    }
    row = insert_one("Claim", record)
    log_entity_change(
        "claim",
        claim_id,
        user_id,
        {
            "action": "created",
            "product_id": product_id,
            "fields": body.model_dump(exclude_none=True),
        },
    )
    return row


@router.post("/{product_id}/claims/{claim_id}/evidence", status_code=201)
async def create_evidence(
    product_id: str,
    claim_id: str,
    body: EvidenceCreate,
    user_id: str = Depends(get_current_user_id),
    _verifier: UserRole = Depends(require_verifier),
):
    """Add evidence to a claim. Requires verifier role."""
    validate_uuid(product_id, "product_id")
    validate_uuid(claim_id, "claim_id")

    claim = select_by_id(Claim, "claim_id", claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    evidence_id = str(uuid.uuid4())
    record = {
        "evidence_id": evidence_id,
        "claim_id": claim_id,
        **body.model_dump(exclude_none=True),
        "created_at": datetime.now().isoformat(),
    }
    row = insert_one("Evidence", record)
    log_entity_change(
        "evidence",
        evidence_id,
        user_id,
        {
            "action": "created",
            "claim_id": claim_id,
            "fields": body.model_dump(exclude_none=True),
        },
    )
    return row


@router.post("/{product_id}/evidence/upload", status_code=201)
async def upload_evidence(
    product_id: str,
    file: UploadFile = File(...),
    type: str = Form(...),
    issuer: str = Form(...),
    date: str | None = Form(None),
    summary: str | None = Form(None),
    claim_id: str | None = Form(None),
    stage_id: str | None = Form(None),
    user_id: str = Depends(get_current_user_id),
    _verifier: UserRole = Depends(require_verifier),
):
    """Upload evidence for either a claim or a stage. Requires verifier role."""
    validate_uuid(product_id, "product_id")
    product = select_by_id(Product, "product_id", product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # only accept pdf or txt
    if file.content_type not in {"application/pdf", "text/plain"}:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and text files are allowed",
        )

    target = validate_evidence_target(product_id, claim_id, stage_id)

    # cap at 1MB (supabase free tier is 50mb storage)
    contents = await file.read()
    if len(contents) > 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be 1MB or less")

    evidence_id = str(uuid.uuid4())
    safe_name = normalize_filename(file.filename)

    # link to either claim or stage
    if target["claim"] is not None:
        object_path = (
            f"products/{product_id}/claims/{claim_id}/{evidence_id}-{safe_name}"
        )
    else:
        object_path = (
            f"products/{product_id}/stages/{stage_id}/{evidence_id}-{safe_name}"
        )

    client = get_client()
    client.storage.from_("documents").upload(
        object_path,
        contents,
        {"content-type": file.content_type},
    )

    record = {
        "evidence_id": evidence_id,
        "type": type,
        "issuer": issuer,
        "file_reference": object_path,
        "created_at": datetime.now().isoformat(),
    }
    if date:
        record["date"] = date
    if summary:
        record["summary"] = summary
    if claim_id:
        record["claim_id"] = claim_id
    if stage_id:
        record["stage_id"] = stage_id

    row = insert_one("Evidence", record)
    log_entity_change(
        "evidence",
        evidence_id,
        user_id,
        {
            "action": "uploaded",
            "product_id": product_id,
            "claim_id": claim_id,
            "stage_id": stage_id,
            "file_reference": object_path,
            "fields": {
                "type": type,
                "issuer": issuer,
                "date": date,
                "summary": summary,
            },
        },
    )
    return row


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
    response = client.table("Claim").select("*").is_("verified_by", "null").execute()

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

    return ProductTraceability(
        product=product,
        stages=stages,
        input_shares=input_shares,
        claims=claims,
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
            groups.append(
                ClaimEvidenceGroup(
                    claim_id=claim.claim_id,
                    claim_type=claim.claim_type,
                    claim_text=claim.claim_text,
                    confidence_label=claim.confidence_label,
                    evidence=evidence,
                )
            )

    return ProductEvidenceView(product_id=product_id, groups=groups)


@router.get("/{product_id}/stage-evidence")
def get_product_stage_evidence(product_id: str) -> ProductStageEvidenceView:
    """Returns evidence grouped by stage for timeline and dashboard views."""
    validate_uuid(product_id, "product_id")
    product = select_by_id(Product, "product_id", product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    stages = select_by_field(Stage, "product_id", product_id)
    stages.sort(key=lambda s: s.sequence_order or 0)
    groups: list[StageEvidenceGroup] = []
    for stage in stages:
        evidence = select_by_field(Evidence, "stage_id", stage.stage_id)
        if evidence:
            groups.append(
                StageEvidenceGroup(
                    stage_id=stage.stage_id,
                    stage_type=stage.stage_type,
                    description=stage.description,
                    evidence=evidence,
                )
            )

    return ProductStageEvidenceView(product_id=product_id, groups=groups)


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

        if not isinstance(options, list) or not all(
            isinstance(o, str) for o in options
        ):
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


@router.get("/{product_id}/claims/{claim_id}/evidence")
def get_claim_evidence(product_id: str, claim_id: str) -> ClaimEvidenceGroup:
    """
    Returns evidence for a single claim, shaped for the drill-down evidence view.
    """
    validate_uuid(product_id, "product_id")
    validate_uuid(claim_id, "claim_id")

    claim = select_by_id(Claim, "claim_id", claim_id)
    if not claim or claim.product_id != product_id:
        raise HTTPException(status_code=404, detail="Claim not found")

    evidence = select_by_field(Evidence, "claim_id", claim_id)
    return ClaimEvidenceGroup(
        claim_id=claim.claim_id,
        claim_type=claim.claim_type,
        claim_text=claim.claim_text,
        confidence_label=claim.confidence_label,
        rationale=claim.rationale,
        evidence=evidence,
    )


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

    # Integrity check: claim must have at least one piece of evidence to be verified
    evidence = select_by_field(Evidence, "claim_id", claim_id)
    if not evidence:
        raise HTTPException(
            status_code=400, detail="Cannot verify a claim with no evidence"
        )

    # Creates connect with db
    # Updates the claim
    client = get_client()
    client.table("Claim").update(
        {
            "verified_by": user_id,
            "verified_at": datetime.now().isoformat(),
            "verification_notes": notes,
            "confidence_label": "verified",
        }
    ).eq("claim_id", claim_id).execute()

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
    client.table("Claim").update(
        {
            "verified_by": None,
            "verified_at": None,
            "verification_notes": notes,  # keep for logs
            "confidence_label": "unverified",
        }
    ).eq("claim_id", claim_id).execute()

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
    client.table("Claim").update({"confidence_label": confidence_label}).eq(
        "claim_id", claim_id
    ).execute()

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
    _verifier: UserRole = Depends(require_verifier),
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
