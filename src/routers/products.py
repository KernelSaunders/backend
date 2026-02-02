from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..models import Product, Stage, InputShare, Claim, Evidence
from ..database import select_all, select_by_id, select_by_field


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


@router.get("")
def get_products() -> list[Product]:
    return select_all(Product)


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
