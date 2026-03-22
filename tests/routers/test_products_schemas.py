"""Unit tests for Pydantic request/response schemas in src.routers.products."""

import pytest
from pydantic import ValidationError

from src.routers.products import (
    ClaimCreate,
    EvidenceCreate,
    ProductCreate,
    ProductUpdate,
    StageCreate,
    StageUpdate,
)


class TestProductCreate:
    def test_valid_full_payload(self):
        body = ProductCreate(
            name="Organic oats",
            category="food",
            brand="Farm Co",
            description="Rolled oats",
            image="https://cdn.example/oats.jpg",
        )
        assert body.name == "Organic oats"
        assert body.category == "food"
        assert body.brand == "Farm Co"
        assert body.description == "Rolled oats"
        assert body.image == "https://cdn.example/oats.jpg"

    def test_minimal_required_fields(self):
        body = ProductCreate(name="X", category="other")
        assert body.name == "X"
        assert body.brand is None
        assert body.description is None
        assert body.image is None

    def test_all_categories_accepted(self):
        for cat in ("food", "luxury", "supplements", "other"):
            assert ProductCreate(name="n", category=cat).category == cat

    def test_invalid_category_rejected(self):
        with pytest.raises(ValidationError) as exc:
            ProductCreate(name="n", category="invalid")  # type: ignore[arg-type]
        assert any(e["loc"] == ("category",) for e in exc.value.errors())

    def test_missing_name_rejected(self):
        with pytest.raises(ValidationError) as exc:
            ProductCreate(category="food")  # type: ignore[call-arg]
        assert any(e["loc"] == ("name",) for e in exc.value.errors())

    def test_model_dump(self):
        d = ProductCreate(name="A", category="luxury").model_dump()
        assert d == {"name": "A", "category": "luxury", "brand": None, "description": None, "image": None}


class TestProductUpdate:
    def test_empty_means_all_none(self):
        body = ProductUpdate()
        assert body.model_dump(exclude_none=True) == {}

    def test_partial_update_fields(self):
        body = ProductUpdate(name="New", brand=None)
        assert body.name == "New"
        assert body.brand is None
        assert body.category is None

    def test_category_literal_valid(self):
        body = ProductUpdate(category="supplements")
        assert body.category == "supplements"

    def test_invalid_category_rejected(self):
        with pytest.raises(ValidationError) as exc:
            ProductUpdate(category="bad")  # type: ignore[arg-type]
        assert any(e["loc"] == ("category",) for e in exc.value.errors())

    def test_roundtrip(self):
        data = {"name": "Z", "description": "d", "image": None}
        assert ProductUpdate(**data).model_dump() == {**data, "category": None, "brand": None}


class TestStageCreate:
    def test_minimal(self):
        body = StageCreate(stage_type="harvest")
        assert body.stage_type == "harvest"
        assert body.location_country is None
        assert body.sequence_order is None

    def test_full_optional_strings_and_order(self):
        body = StageCreate(
            stage_type="pack",
            location_country="US",
            location_region="CA",
            start_date="2024-01-01",
            end_date="2024-12-31",
            description="Packed on site",
            sequence_order=2,
        )
        assert body.sequence_order == 2
        assert body.start_date == "2024-01-01"

    def test_missing_stage_type_rejected(self):
        with pytest.raises(ValidationError) as exc:
            StageCreate()  # type: ignore[call-arg]
        assert any(e["loc"] == ("stage_type",) for e in exc.value.errors())


class TestStageUpdate:
    def test_empty(self):
        assert StageUpdate().model_dump(exclude_none=True) == {}

    def test_any_subset(self):
        body = StageUpdate(description="x", sequence_order=5)
        assert body.stage_type is None
        assert body.description == "x"
        assert body.sequence_order == 5


class TestClaimCreate:
    def test_defaults_unverified_and_optional_rationale(self):
        body = ClaimCreate(claim_type="origin", claim_text="EU sourced")
        assert body.confidence_label == "unverified"
        assert body.rationale is None

    def test_explicit_confidence_literals(self):
        for label in ("verified", "partially_verified", "unverified"):
            b = ClaimCreate(
                claim_type="t",
                claim_text="c",
                confidence_label=label,
                rationale="r" if label == "unverified" else None,
            )
            assert b.confidence_label == label

    def test_invalid_confidence_rejected(self):
        with pytest.raises(ValidationError) as exc:
            ClaimCreate(
                claim_type="t",
                claim_text="c",
                confidence_label="maybe",  # type: ignore[arg-type]
            )
        assert any(e["loc"] == ("confidence_label",) for e in exc.value.errors())

    def test_missing_claim_text_rejected(self):
        with pytest.raises(ValidationError) as exc:
            ClaimCreate(claim_type="t")  # type: ignore[call-arg]
        assert any(e["loc"] == ("claim_text",) for e in exc.value.errors())


class TestEvidenceCreate:
    def test_minimal(self):
        body = EvidenceCreate(type="certificate", issuer="Lab A")
        assert body.date is None
        assert body.stage_id is None

    def test_full(self):
        body = EvidenceCreate(
            type="doc",
            issuer="Gov",
            date="2024-06-01",
            summary="Audit passed",
            file_reference="audit.pdf",
            stage_id="550e8400-e29b-41d4-a716-446655440000",
        )
        assert body.summary == "Audit passed"
        assert body.file_reference == "audit.pdf"

    def test_missing_issuer_rejected(self):
        with pytest.raises(ValidationError) as exc:
            EvidenceCreate(type="x")  # type: ignore[call-arg]
        assert any(e["loc"] == ("issuer",) for e in exc.value.errors())

    def test_missing_type_rejected(self):
        with pytest.raises(ValidationError) as exc:
            EvidenceCreate(issuer="x")  # type: ignore[call-arg]
        assert any(e["loc"] == ("type",) for e in exc.value.errors())
