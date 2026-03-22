"""Unit tests for Pydantic schemas in src.routers.issues."""

import pytest
from pydantic import ValidationError

from src.routers.issues import IssueCreate, IssueUpdate


class TestIssueCreate:
    def test_valid_payload(self):
        body = IssueCreate(
            product_id="550e8400-e29b-41d4-a716-446655440000",
            type="claim_false",
            description="This claim contradicts the label",
        )
        assert body.product_id == "550e8400-e29b-41d4-a716-446655440000"
        assert body.type == "claim_false"
        assert "contradicts" in body.description

    def test_all_issue_types_accepted(self):
        for t in ("claim_false", "evidence_missing", "data_incorrect", "other"):
            b = IssueCreate(product_id="p", type=t, description="d")
            assert b.type == t

    def test_invalid_type_rejected(self):
        with pytest.raises(ValidationError) as exc:
            IssueCreate(product_id="p", type="unknown", description="d")  # type: ignore[arg-type]
        assert any(e["loc"] == ("type",) for e in exc.value.errors())

    def test_missing_product_id_rejected(self):
        with pytest.raises(ValidationError) as exc:
            IssueCreate(type="other", description="d")  # type: ignore[call-arg]
        assert any(e["loc"] == ("product_id",) for e in exc.value.errors())

    def test_missing_description_rejected(self):
        with pytest.raises(ValidationError) as exc:
            IssueCreate(product_id="p", type="other")  # type: ignore[call-arg]
        assert any(e["loc"] == ("description",) for e in exc.value.errors())

    def test_model_dump(self):
        d = IssueCreate(
            product_id="550e8400-e29b-41d4-a716-446655440000",
            type="evidence_missing",
            description="No cert on file",
        ).model_dump()
        assert d["type"] == "evidence_missing"


class TestIssueUpdate:
    def test_status_only(self):
        body = IssueUpdate(status="under_review")
        assert body.status == "under_review"
        assert body.resolution_note is None

    def test_status_with_resolution_note(self):
        body = IssueUpdate(status="resolved", resolution_note="Fixed in v2")
        assert body.status == "resolved"
        assert body.resolution_note == "Fixed in v2"

    def test_all_status_literals(self):
        for s in ("open", "under_review", "resolved", "rejected"):
            assert IssueUpdate(status=s).status == s

    def test_invalid_status_rejected(self):
        with pytest.raises(ValidationError) as exc:
            IssueUpdate(status="closed")  # type: ignore[arg-type]
        assert any(e["loc"] == ("status",) for e in exc.value.errors())

    def test_missing_status_rejected(self):
        with pytest.raises(ValidationError) as exc:
            IssueUpdate()  # type: ignore[call-arg]
        assert any(e["loc"] == ("status",) for e in exc.value.errors())

    def test_resolution_note_explicitly_none(self):
        body = IssueUpdate(status="open", resolution_note=None)
        assert body.resolution_note is None
