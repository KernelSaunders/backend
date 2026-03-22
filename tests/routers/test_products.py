"""Tests for products router."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.auth import get_current_user_id, get_current_user_role
from src.main import app
from src.models import Claim, Evidence, InputShare, Product, Stage
from src.models.user import QuestMission, UserRole
from src.routers.products import (
    ClaimEvidenceGroup,
    ClaimWithEvidence,
    ProductEvidenceView,
    ProductTraceability,
    QuestMissionPublic,
    validate_uuid,
)

from tests.conftest import TEST_USER_ID

PID = "550e8400-e29b-41d4-a716-446655440000"
CLAIM_ID = "223e4567-e89b-12d3-a456-426614174001"
STAGE_ID = "323e4567-e89b-12d3-a456-426614174002"
MISSION_ID = "423e4567-e89b-12d3-a456-426614174003"


def _sample_product(product_id: str = PID) -> Product:
    return Product(
        product_id=product_id,
        name="Test Product",
        category="food",
        brand="Brand",
        description="Desc",
        image=None,
        created_at=datetime(2024, 1, 1, 0, 0, 0),
        updated_at=datetime(2024, 1, 2, 0, 0, 0),
    )


def _sample_stage(
    stage_id: str = STAGE_ID,
    product_id: str = PID,
    sequence_order: int | None = 1,
) -> Stage:
    return Stage(
        stage_id=stage_id,
        product_id=product_id,
        stage_type="production",
        sequence_order=sequence_order,
        created_at=datetime(2024, 1, 1, 0, 0, 0),
    )


def _sample_claim(
    claim_id: str = CLAIM_ID,
    product_id: str = PID,
    confidence: str = "unverified",
) -> Claim:
    return Claim(
        claim_id=claim_id,
        product_id=product_id,
        claim_type="origin",
        claim_text="Made in EU",
        confidence_label=confidence,
        rationale="Pending review",
        created_at=datetime(2024, 1, 1, 0, 0, 0),
        updated_at=datetime(2024, 1, 1, 0, 0, 0),
    )


def _sample_evidence(claim_id: str = CLAIM_ID) -> Evidence:
    return Evidence(
        evidence_id="523e4567-e89b-12d3-a456-426614174004",
        claim_id=claim_id,
        type="cert",
        issuer="Lab",
        created_at=datetime(2024, 1, 1, 0, 0, 0),
    )


class TestValidateUuid:
    """Test suite for validate_uuid utility function."""

    def test_validate_uuid_with_valid_uuid(self):
        """Test that valid UUID strings are accepted."""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        result = validate_uuid(valid_uuid)
        assert result == valid_uuid

    def test_validate_uuid_with_valid_uuid_different_format(self):
        """Test that valid UUID strings in different formats are accepted."""
        valid_uuids = [
            "123e4567-e89b-12d3-a456-426614174000",
            "00000000-0000-0000-0000-000000000000",
            "ffffffff-ffff-ffff-ffff-ffffffffffff",
            "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        ]
        for uuid in valid_uuids:
            result = validate_uuid(uuid)
            assert result == uuid

    def test_validate_uuid_with_invalid_uuid(self):
        """Test that invalid UUID strings raise HTTPException."""
        invalid_uuid = "not-a-valid-uuid"
        with pytest.raises(HTTPException) as exc_info:
            validate_uuid(invalid_uuid)
        assert exc_info.value.status_code == 400
        assert "Invalid id format" in exc_info.value.detail

    def test_validate_uuid_with_invalid_uuid_formats(self):
        """Test that various invalid UUID formats raise HTTPException."""
        invalid_uuids = [
            "12345",
            "not-a-uuid-at-all",
            "550e8400-e29b-41d4-a716",  # Too short
            "550e8400-e29b-41d4-a716-446655440000-extra",  # Too long
            "550e8400-e29b-41d4-a716-44665544000g",  # Invalid character
        ]
        for invalid_uuid in invalid_uuids:
            with pytest.raises(HTTPException) as exc_info:
                validate_uuid(invalid_uuid)
            assert exc_info.value.status_code == 400

    def test_validate_uuid_with_custom_field_name(self):
        """Test that custom field_name is used in error message."""
        invalid_uuid = "invalid-uuid"
        with pytest.raises(HTTPException) as exc_info:
            validate_uuid(invalid_uuid, "product_id")
        assert exc_info.value.status_code == 400
        assert "Invalid product_id format" in exc_info.value.detail

    def test_validate_uuid_returns_value_on_success(self):
        """Test that validate_uuid returns the value when valid."""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        result = validate_uuid(valid_uuid, "custom_field")
        assert result == valid_uuid
        assert isinstance(result, str)


class TestGetProducts:
    """Test suite for GET /products endpoint."""

    def setup_method(self):
        self.client = TestClient(app)

    @patch("src.routers.products.select_all")
    def test_get_products_returns_list(self, mock_select_all):
        p = _sample_product()
        mock_select_all.return_value = [p]
        response = self.client.get("/products")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["product_id"] == PID

    @patch("src.routers.products.select_all")
    def test_get_products_empty_database(self, mock_select_all):
        mock_select_all.return_value = []
        response = self.client.get("/products")
        assert response.status_code == 200
        assert response.json() == []

    @patch("src.routers.products.select_all")
    def test_get_products_calls_select_all(self, mock_select_all):
        mock_select_all.return_value = []
        self.client.get("/products")
        mock_select_all.assert_called_once()
        assert mock_select_all.call_args[0][0] is Product

    @patch("src.routers.products.select_all")
    def test_get_products_response_status_code(self, mock_select_all):
        mock_select_all.return_value = []
        assert self.client.get("/products").status_code == 200

    @patch("src.routers.products.select_all")
    def test_get_products_response_structure(self, mock_select_all):
        mock_select_all.return_value = [_sample_product()]
        data = self.client.get("/products").json()
        assert "product_id" in data[0]
        assert "name" in data[0]
        assert "category" in data[0]


class TestGetProduct:
    """Test suite for GET /products/{product_id} endpoint - Product ID Search Feature."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.client = TestClient(app)
        self.valid_product_id = "550e8400-e29b-41d4-a716-446655440000"
        self.mock_product = Product(
            product_id=self.valid_product_id,
            name="Test Product",
            category="food",
            brand="Test Brand",
            description="Test description",
            image="https://example.com/image.jpg",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )

    @patch("src.routers.products.select_by_id")
    def test_get_product_with_valid_id(self, mock_select_by_id):
        """Test that GET /products/{id} returns product with valid ID."""
        mock_select_by_id.return_value = self.mock_product

        response = self.client.get(f"/products/{self.valid_product_id}")

        assert response.status_code == 200
        assert response.json()["product_id"] == self.valid_product_id
        assert response.json()["name"] == "Test Product"
        mock_select_by_id.assert_called_once_with(
            Product, "product_id", self.valid_product_id
        )

    @patch("src.routers.products.select_by_id")
    def test_get_product_search_by_id_returns_correct_product(self, mock_select_by_id):
        """Test that searching by product ID returns the correct product data."""
        mock_select_by_id.return_value = self.mock_product

        response = self.client.get(f"/products/{self.valid_product_id}")
        data = response.json()

        assert data["product_id"] == self.valid_product_id
        assert data["name"] == "Test Product"
        assert data["category"] == "food"
        assert data["brand"] == "Test Brand"
        assert data["description"] == "Test description"
        assert data["image"] == "https://example.com/image.jpg"

    def test_get_product_with_invalid_uuid(self):
        """Test that GET /products/{id} returns 400 for invalid UUID."""
        invalid_ids = [
            "invalid-uuid",
            "12345",
            "not-a-uuid-at-all",
            "550e8400-e29b-41d4-a716",  # Too short
        ]

        for invalid_id in invalid_ids:
            response = self.client.get(f"/products/{invalid_id}")
            assert response.status_code == 400
            assert "Invalid product_id format" in response.json()["detail"]

    @patch("src.routers.products.select_by_id")
    def test_get_product_not_found(self, mock_select_by_id):
        """Test that GET /products/{id} returns 404 when product not found."""
        mock_select_by_id.return_value = None
        non_existent_id = "123e4567-e89b-12d3-a456-426614174000"

        response = self.client.get(f"/products/{non_existent_id}")

        assert response.status_code == 404
        assert "Product not found" in response.json()["detail"]
        mock_select_by_id.assert_called_once_with(
            Product, "product_id", non_existent_id
        )

    @patch("src.routers.products.select_by_id")
    def test_get_product_calls_select_by_id(self, mock_select_by_id):
        """Test that get_product calls select_by_id with correct parameters."""
        mock_select_by_id.return_value = self.mock_product

        self.client.get(f"/products/{self.valid_product_id}")

        mock_select_by_id.assert_called_once()
        call_args = mock_select_by_id.call_args
        assert call_args[0][0] == Product
        assert call_args[0][1] == "product_id"
        assert call_args[0][2] == self.valid_product_id

    @patch("src.routers.products.select_by_id")
    def test_get_product_validates_uuid_before_database_query(self, mock_select_by_id):
        """Test that UUID validation happens before database query."""
        invalid_id = "not-a-uuid"

        response = self.client.get(f"/products/{invalid_id}")

        assert response.status_code == 400
        # Database should not be called if UUID is invalid
        mock_select_by_id.assert_not_called()

    @patch("src.routers.products.select_by_id")
    def test_get_product_with_different_valid_uuids(self, mock_select_by_id):
        """Test product search with multiple different valid UUIDs."""
        test_cases = [
            ("123e4567-e89b-12d3-a456-426614174000", "Product A"),
            ("987f6543-e21b-12d3-a456-426614174999", "Product B"),
            ("aaaabbbb-cccc-dddd-eeee-ffffffffffff", "Product C"),
        ]

        for product_id, product_name in test_cases:
            mock_product = Product(
                product_id=product_id,
                name=product_name,
                category="food",
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00",
            )
            mock_select_by_id.return_value = mock_product

            response = self.client.get(f"/products/{product_id}")

            assert response.status_code == 200
            assert response.json()["product_id"] == product_id
            assert response.json()["name"] == product_name

    @patch("src.routers.products.select_by_id")
    def test_get_product_response_structure(self, mock_select_by_id):
        """Test that GET /products/{id} returns correctly structured response."""
        mock_select_by_id.return_value = self.mock_product

        response = self.client.get(f"/products/{self.valid_product_id}")
        data = response.json()

        assert response.status_code == 200
        # Verify all expected fields are present
        assert "product_id" in data
        assert "name" in data
        assert "category" in data
        assert "brand" in data
        assert "description" in data
        assert "image" in data
        assert "created_at" in data
        assert "updated_at" in data

    @patch("src.routers.products.select_by_id")
    def test_get_product_with_minimal_data(self, mock_select_by_id):
        """Test product search returns correctly even with minimal product data."""
        minimal_product = Product(
            product_id=self.valid_product_id,
            name="Minimal Product",
            category="other",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        mock_select_by_id.return_value = minimal_product

        response = self.client.get(f"/products/{self.valid_product_id}")
        data = response.json()

        assert response.status_code == 200
        assert data["product_id"] == self.valid_product_id
        assert data["name"] == "Minimal Product"
        assert data["brand"] is None
        assert data["description"] is None
        assert data["image"] is None

    @patch("src.routers.products.select_by_id")
    def test_get_product_search_performance_single_query(self, mock_select_by_id):
        """Test that product search makes only one database query."""
        mock_select_by_id.return_value = self.mock_product

        self.client.get(f"/products/{self.valid_product_id}")

        # Verify select_by_id is called exactly once
        assert mock_select_by_id.call_count == 1

    @patch("src.routers.products.select_by_id")
    def test_get_product_handles_database_errors_gracefully(self, mock_select_by_id):
        """Test that database errors are handled appropriately."""
        mock_select_by_id.side_effect = Exception("Database connection error")

        with pytest.raises(Exception):
            self.client.get(f"/products/{self.valid_product_id}")

    @patch("src.routers.products.select_by_id")
    def test_get_product_case_sensitive_uuid_search(self, mock_select_by_id):
        """Test that UUID search handles case variations correctly."""
        # UUIDs should be case-insensitive
        uuid_lowercase = "550e8400-e29b-41d4-a716-446655440000"
        uuid_uppercase = "550E8400-E29B-41D4-A716-446655440000"

        mock_select_by_id.return_value = self.mock_product

        response_lower = self.client.get(f"/products/{uuid_lowercase}")
        response_upper = self.client.get(f"/products/{uuid_uppercase}")

        # Both should be valid UUIDs
        assert response_lower.status_code == 200
        assert response_upper.status_code == 200


class TestGetProductTraceability:
    """Test suite for GET /products/{product_id}/traceability endpoint."""

    def setup_method(self):
        self.client = TestClient(app)

    def _patch_traceability(self, mock_select_by_id, mock_select_by_field, product, stages, shares, claims):
        mock_select_by_id.return_value = product

        def by_field(model, field, value):
            if model is Stage:
                return list(stages)
            if model is InputShare:
                return list(shares)
            if model is Claim:
                return list(claims)
            return []

        mock_select_by_field.side_effect = by_field

    @patch("src.routers.products.select_by_field")
    @patch("src.routers.products.select_by_id")
    def test_get_product_traceability_with_valid_id(self, mock_select_by_id, mock_select_by_field):
        product = _sample_product()
        stages = [_sample_stage()]
        shares = [
            InputShare(
                input_id="i1",
                product_id=PID,
                input_name="wheat",
                country="US",
                created_at=datetime(2024, 1, 1),
            )
        ]
        claims = [_sample_claim()]
        self._patch_traceability(
            mock_select_by_id, mock_select_by_field, product, stages, shares, claims
        )
        r = self.client.get(f"/products/{PID}/traceability")
        assert r.status_code == 200
        body = r.json()
        assert body["product"]["product_id"] == PID
        assert len(body["stages"]) == 1
        assert len(body["input_shares"]) == 1
        assert len(body["claims"]) == 1

    def test_get_product_traceability_with_invalid_uuid(self):
        r = self.client.get("/products/not-a-uuid/traceability")
        assert r.status_code == 400

    @patch("src.routers.products.select_by_field")
    @patch("src.routers.products.select_by_id")
    def test_get_product_traceability_product_not_found(self, mock_select_by_id, mock_select_by_field):
        mock_select_by_id.return_value = None
        r = self.client.get(f"/products/{PID}/traceability")
        assert r.status_code == 404
        mock_select_by_field.assert_not_called()

    @patch("src.routers.products.select_by_field")
    @patch("src.routers.products.select_by_id")
    def test_get_product_traceability_includes_stages(self, mock_select_by_id, mock_select_by_field):
        s1, s2 = _sample_stage(STAGE_ID, PID, 1), _sample_stage(
            "333e4567-e89b-12d3-a456-426614174099", PID, 2
        )
        self._patch_traceability(
            mock_select_by_id, mock_select_by_field, _sample_product(), [s1, s2], [], []
        )
        stages = self.client.get(f"/products/{PID}/traceability").json()["stages"]
        assert {s["stage_id"] for s in stages} == {s1.stage_id, s2.stage_id}

    @patch("src.routers.products.select_by_field")
    @patch("src.routers.products.select_by_id")
    def test_get_product_traceability_stages_sorted_by_sequence(self, mock_select_by_id, mock_select_by_field):
        late = _sample_stage("11111111-1111-1111-1111-111111111111", PID, 10)
        early = _sample_stage("22222222-2222-2222-2222-222222222222", PID, 1)
        none_order = _sample_stage("33333333-3333-3333-3333-333333333333", PID, None)
        self._patch_traceability(
            mock_select_by_id,
            mock_select_by_field,
            _sample_product(),
            [late, early, none_order],
            [],
            [],
        )
        ordered = self.client.get(f"/products/{PID}/traceability").json()["stages"]
        assert [s["stage_id"] for s in ordered] == [
            none_order.stage_id,
            early.stage_id,
            late.stage_id,
        ]

    @patch("src.routers.products.select_by_field")
    @patch("src.routers.products.select_by_id")
    def test_get_product_traceability_includes_input_shares(self, mock_select_by_id, mock_select_by_field):
        share = InputShare(
            input_id="inp-1",
            product_id=PID,
            input_name="sugar",
            country="BR",
            created_at=datetime(2024, 1, 1),
        )
        self._patch_traceability(mock_select_by_id, mock_select_by_field, _sample_product(), [], [share], [])
        rows = self.client.get(f"/products/{PID}/traceability").json()["input_shares"]
        assert len(rows) == 1 and rows[0]["input_name"] == "sugar"

    @patch("src.routers.products.select_by_field")
    @patch("src.routers.products.select_by_id")
    def test_get_product_traceability_includes_claims_with_evidence(self, mock_select_by_id, mock_select_by_field):
        """Traceability lists claims (evidence is on separate endpoints)."""
        claim = _sample_claim()
        self._patch_traceability(mock_select_by_id, mock_select_by_field, _sample_product(), [], [], [claim])
        rows = self.client.get(f"/products/{PID}/traceability").json()["claims"]
        assert len(rows) == 1 and rows[0]["claim_text"] == "Made in EU"

    @patch("src.routers.products.select_by_field")
    @patch("src.routers.products.select_by_id")
    def test_get_product_traceability_response_status_code(self, mock_select_by_id, mock_select_by_field):
        self._patch_traceability(
            mock_select_by_id, mock_select_by_field, _sample_product(), [], [], []
        )
        assert self.client.get(f"/products/{PID}/traceability").status_code == 200

    @patch("src.routers.products.select_by_field")
    @patch("src.routers.products.select_by_id")
    def test_get_product_traceability_response_structure(self, mock_select_by_id, mock_select_by_field):
        self._patch_traceability(
            mock_select_by_id, mock_select_by_field, _sample_product(), [], [], []
        )
        body = self.client.get(f"/products/{PID}/traceability").json()
        assert set(body.keys()) == {"product", "stages", "input_shares", "claims"}
        assert isinstance(body["stages"], list)
        assert isinstance(body["input_shares"], list)
        assert isinstance(body["claims"], list)

    @patch("src.routers.products.select_by_field")
    @patch("src.routers.products.select_by_id")
    def test_get_product_traceability_with_no_claims(self, mock_select_by_id, mock_select_by_field):
        self._patch_traceability(
            mock_select_by_id, mock_select_by_field, _sample_product(), [_sample_stage()], [], []
        )
        assert self.client.get(f"/products/{PID}/traceability").json()["claims"] == []

    @patch("src.routers.products.select_by_field")
    @patch("src.routers.products.select_by_id")
    def test_get_product_traceability_with_no_stages(self, mock_select_by_id, mock_select_by_field):
        self._patch_traceability(mock_select_by_id, mock_select_by_field, _sample_product(), [], [], [])
        assert self.client.get(f"/products/{PID}/traceability").json()["stages"] == []

    @patch("src.routers.products.select_by_field")
    @patch("src.routers.products.select_by_id")
    def test_get_product_traceability_with_no_input_shares(self, mock_select_by_id, mock_select_by_field):
        self._patch_traceability(mock_select_by_id, mock_select_by_field, _sample_product(), [], [], [])
        assert self.client.get(f"/products/{PID}/traceability").json()["input_shares"] == []


class TestClaimWithEvidence:
    """Test suite for ClaimWithEvidence model."""

    def test_claim_with_evidence_initialization(self):
        claim = _sample_claim()
        ev = _sample_evidence()
        cwe = ClaimWithEvidence(claim=claim, evidence=[ev])
        assert cwe.claim.claim_id == CLAIM_ID
        assert len(cwe.evidence) == 1
        assert cwe.evidence[0].evidence_id == ev.evidence_id

    def test_claim_with_evidence_serialization(self):
        cwe = ClaimWithEvidence(claim=_sample_claim(), evidence=[_sample_evidence()])
        d = cwe.model_dump()
        assert d["claim"]["claim_id"] == CLAIM_ID
        assert d["evidence"][0]["issuer"] == "Lab"


class TestProductTraceability:
    """Test suite for ProductTraceability model."""

    def test_product_traceability_initialization(self):
        pt = ProductTraceability(
            product=_sample_product(),
            stages=[_sample_stage()],
            input_shares=[],
            claims=[_sample_claim()],
        )
        assert pt.product.product_id == PID
        assert len(pt.stages) == 1
        assert pt.input_shares == []
        assert len(pt.claims) == 1

    def test_product_traceability_serialization(self):
        pt = ProductTraceability(
            product=_sample_product(),
            stages=[],
            input_shares=[],
            claims=[],
        )
        d = pt.model_dump()
        assert d["product"]["name"] == "Test Product"
        assert d["stages"] == []


class TestUpdateProduct:
    @patch("src.routers.products.log_entity_change")
    @patch("src.routers.products.update_by_id")
    @patch("src.routers.products.select_by_id")
    def test_update_product_success(self, mock_select, mock_update, mock_log, verifier_client):
        mock_select.return_value = _sample_product()
        mock_update.return_value = {"product_id": PID, "name": "New"}
        r = verifier_client.put(f"/products/{PID}", json={"name": "New"})
        assert r.status_code == 200
        mock_update.assert_called_once()
        mock_log.assert_called_once()

    @patch("src.routers.products.select_by_id")
    def test_update_product_not_found(self, mock_select, verifier_client):
        mock_select.return_value = None
        r = verifier_client.put(f"/products/{PID}", json={"name": "X"})
        assert r.status_code == 404

    @patch("src.routers.products.select_by_id")
    def test_update_product_no_fields_returns_400(self, mock_select, verifier_client):
        mock_select.return_value = _sample_product()
        r = verifier_client.put(f"/products/{PID}", json={})
        assert r.status_code == 400
        assert "No fields" in r.json()["detail"]

    def test_update_product_invalid_uuid(self, verifier_client):
        r = verifier_client.put("/products/bad-uuid", json={"name": "X"})
        assert r.status_code == 400


class TestCreateStage:
    @patch("src.routers.products.log_entity_change")
    @patch("src.routers.products.insert_one")
    @patch("src.routers.products.select_by_id")
    def test_create_stage_success(self, mock_sel, mock_ins, mock_log, verifier_client):
        mock_sel.return_value = _sample_product()
        mock_ins.return_value = {"stage_id": STAGE_ID}
        body = {"stage_type": "harvest"}
        r = verifier_client.post(f"/products/{PID}/stages", json=body)
        assert r.status_code == 201
        mock_ins.assert_called_once()
        assert mock_ins.call_args[0][0] == "Stage"
        mock_log.assert_called_once()

    @patch("src.routers.products.select_by_id")
    def test_create_stage_product_not_found(self, mock_sel, verifier_client):
        mock_sel.return_value = None
        r = verifier_client.post(f"/products/{PID}/stages", json={"stage_type": "x"})
        assert r.status_code == 404

    def test_create_stage_invalid_product_uuid_returns_400(self, verifier_client):
        r = verifier_client.post(
            "/products/not-a-uuid/stages", json={"stage_type": "x"}
        )
        assert r.status_code == 400
        assert "product_id" in r.json()["detail"] or "Invalid" in r.json()["detail"]


class TestUpdateStage:
    @patch("src.routers.products.log_entity_change")
    @patch("src.routers.products.update_by_id")
    @patch("src.routers.products.select_by_id")
    def test_update_stage_success(self, mock_sel, mock_upd, mock_log, verifier_client):
        mock_sel.return_value = _sample_stage()
        mock_upd.return_value = {"stage_id": STAGE_ID}
        r = verifier_client.put(
            f"/products/{PID}/stages/{STAGE_ID}", json={"description": "updated"}
        )
        assert r.status_code == 200
        mock_log.assert_called_once()

    @patch("src.routers.products.select_by_id")
    def test_update_stage_not_found(self, mock_sel, verifier_client):
        mock_sel.return_value = None
        r = verifier_client.put(
            f"/products/{PID}/stages/{STAGE_ID}", json={"description": "x"}
        )
        assert r.status_code == 404

    @patch("src.routers.products.select_by_id")
    def test_update_stage_empty_body(self, mock_sel, verifier_client):
        mock_sel.return_value = _sample_stage()
        r = verifier_client.put(f"/products/{PID}/stages/{STAGE_ID}", json={})
        assert r.status_code == 400

    def test_update_stage_invalid_stage_uuid_returns_400(self, verifier_client):
        r = verifier_client.put(
            f"/products/{PID}/stages/not-a-uuid", json={"description": "x"}
        )
        assert r.status_code == 400
        assert "stage_id" in r.json()["detail"]

    def test_update_stage_invalid_product_uuid_returns_400(self, verifier_client):
        r = verifier_client.put(
            f"/products/bad-uuid/stages/{STAGE_ID}", json={"description": "x"}
        )
        assert r.status_code == 400
        assert "product_id" in r.json()["detail"]


class TestCreateClaim:
    @patch("src.routers.products.log_entity_change")
    @patch("src.routers.products.insert_one")
    @patch("src.routers.products.select_by_id")
    def test_create_claim_success(self, mock_sel, mock_ins, mock_log, verifier_client):
        mock_sel.return_value = _sample_product()
        mock_ins.return_value = {"claim_id": CLAIM_ID}
        body = {
            "claim_type": "organic",
            "claim_text": "Organic",
            "confidence_label": "unverified",
            "rationale": "Awaiting docs",
        }
        r = verifier_client.post(f"/products/{PID}/claims", json=body)
        assert r.status_code == 201
        mock_log.assert_called_once()

    @patch("src.routers.products.select_by_id")
    def test_create_claim_rejects_non_unverified_confidence(self, mock_sel, verifier_client):
        mock_sel.return_value = _sample_product()
        body = {
            "claim_type": "organic",
            "claim_text": "Organic",
            "confidence_label": "verified",
            "rationale": "x",
        }
        r = verifier_client.post(f"/products/{PID}/claims", json=body)
        assert r.status_code == 400

    @patch("src.routers.products.select_by_id")
    def test_create_claim_requires_rationale_when_unverified(self, mock_sel, verifier_client):
        mock_sel.return_value = _sample_product()
        body = {
            "claim_type": "organic",
            "claim_text": "Organic",
            "confidence_label": "unverified",
        }
        r = verifier_client.post(f"/products/{PID}/claims", json=body)
        assert r.status_code == 400

    @patch("src.routers.products.select_by_id")
    def test_create_claim_product_not_found(self, mock_sel, verifier_client):
        mock_sel.return_value = None
        body = {
            "claim_type": "organic",
            "claim_text": "Organic",
            "confidence_label": "unverified",
            "rationale": "r",
        }
        r = verifier_client.post(f"/products/{PID}/claims", json=body)
        assert r.status_code == 404


class TestCreateEvidence:
    @patch("src.routers.products.log_entity_change")
    @patch("src.routers.products.insert_one")
    @patch("src.routers.products.select_by_id")
    def test_create_evidence_success(self, mock_sel, mock_ins, mock_log, verifier_client):
        mock_sel.return_value = _sample_claim()
        mock_ins.return_value = {"evidence_id": "e1"}
        body = {"type": "doc", "issuer": "Gov"}
        r = verifier_client.post(
            f"/products/{PID}/claims/{CLAIM_ID}/evidence", json=body
        )
        assert r.status_code == 201
        mock_log.assert_called_once()

    @patch("src.routers.products.select_by_id")
    def test_create_evidence_claim_not_found(self, mock_sel, verifier_client):
        mock_sel.return_value = None
        r = verifier_client.post(
            f"/products/{PID}/claims/{CLAIM_ID}/evidence",
            json={"type": "doc", "issuer": "Gov"},
        )
        assert r.status_code == 404

    @patch("src.routers.products.select_by_id")
    def test_create_evidence_invalid_product_uuid_returns_400(self, mock_sel, verifier_client):
        r = verifier_client.post(
            f"/products/not-a-uuid/claims/{CLAIM_ID}/evidence",
            json={"type": "doc", "issuer": "Gov"},
        )
        assert r.status_code == 400
        assert "product_id" in r.json()["detail"]
        mock_sel.assert_not_called()

    @patch("src.routers.products.select_by_id")
    def test_create_evidence_invalid_claim_uuid_returns_400(self, mock_sel, verifier_client):
        r = verifier_client.post(
            f"/products/{PID}/claims/not-a-uuid/evidence",
            json={"type": "doc", "issuer": "Gov"},
        )
        assert r.status_code == 400
        assert "claim_id" in r.json()["detail"]
        mock_sel.assert_not_called()


class TestGetPendingClaims:
    def test_get_pending_claims_returns_rows(self, verifier_client):
        mock_resp = MagicMock()
        mock_resp.data = [{"claim_id": CLAIM_ID, "verified_by": None}]
        mock_table = MagicMock()
        mock_table.select.return_value.is_.return_value.execute.return_value = mock_resp
        mock_client = MagicMock()
        mock_client.table.return_value = mock_table
        with patch("src.routers.products.get_client", return_value=mock_client):
            r = verifier_client.get("/products/claims/pending")
        assert r.status_code == 200
        assert r.json() == mock_resp.data
        mock_client.table.assert_called_with("Claim")


class TestGetPendingClaimsAuthRequired:
    """GET /products/claims/pending without dependency overrides."""

    def setup_method(self):
        self.client = TestClient(app)

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_missing_authorization_returns_422(self):
        app.dependency_overrides.clear()
        r = self.client.get("/products/claims/pending")
        assert r.status_code == 422
        assert any(
            e.get("loc") == ["header", "authorization"] and e.get("type") == "missing"
            for e in r.json()["detail"]
        )

    def test_invalid_bearer_token_returns_401(self):
        app.dependency_overrides.clear()
        mock_auth = MagicMock()
        mock_auth.auth.get_user.side_effect = Exception("invalid")

        with patch("src.auth.get_client", return_value=mock_auth):
            r = self.client.get(
                "/products/claims/pending",
                headers={"Authorization": "Bearer bad"},
            )

        assert r.status_code == 401
        assert r.json()["detail"] == "Invalid token"

    def test_authenticated_consumer_returns_403(self):
        """Valid JWT path but UserRole is not verifier → require_verifier rejects."""
        app.dependency_overrides.clear()
        uid = "99999999-9999-9999-9999-999999999999"
        mock_user = MagicMock()
        mock_user.id = uid
        mock_auth_resp = MagicMock()
        mock_auth_resp.user = mock_user
        mock_supa = MagicMock()
        mock_supa.auth.get_user.return_value = mock_auth_resp

        consumer_role = UserRole(
            role_id="role-consumer",
            user_id=uid,
            role="consumer",
            created_at=datetime(2026, 1, 1),
        )

        with patch("src.auth.get_client", return_value=mock_supa):
            with patch("src.auth.select_by_field", return_value=[consumer_role]):
                r = self.client.get(
                    "/products/claims/pending",
                    headers={"Authorization": "Bearer valid.jwt.token"},
                )

        assert r.status_code == 403
        assert r.json()["detail"] == "Access forbidden: verifier role required"


class TestGetProductEvidence:
    @patch("src.routers.products.select_by_field")
    @patch("src.routers.products.select_by_id")
    def test_groups_only_claims_with_evidence(self, mock_sid, mock_sfield, client):
        mock_sid.return_value = _sample_product()
        claim_with = _sample_claim("c1")
        claim_empty = _sample_claim("c2")
        ev = _sample_evidence("c1")

        def field(model, field_name, value):
            if model is Claim:
                return [claim_with, claim_empty]
            if model is Evidence:
                return [ev] if value == "c1" else []
            return []

        mock_sfield.side_effect = field
        r = client.get(f"/products/{PID}/evidence")
        assert r.status_code == 200
        body = r.json()
        assert body["product_id"] == PID
        assert len(body["groups"]) == 1
        assert body["groups"][0]["claim_id"] == "c1"

    @patch("src.routers.products.select_by_id")
    def test_product_not_found(self, mock_sid, client):
        mock_sid.return_value = None
        assert client.get(f"/products/{PID}/evidence").status_code == 404

    def test_invalid_product_uuid_returns_400(self, client):
        r = client.get("/products/not-a-uuid/evidence")
        assert r.status_code == 400
        assert "product_id" in r.json()["detail"]


class TestGetProductMissions:
    @patch("src.routers.products.select_by_field")
    @patch("src.routers.products.select_by_id")
    def test_returns_auto_missions_with_options(self, mock_sid, mock_sfield, client):
        mock_sid.return_value = _sample_product()
        auto = QuestMission(
            mission_id=MISSION_ID,
            product_id=PID,
            tier="basic",
            question="Q?",
            answer_key={"options": ["A", "B"], "correct": "A"},
            grading_type="auto",
            explanation_link=None,
            created_at=datetime(2024, 1, 1),
        )
        manual = QuestMission(
            mission_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            product_id=PID,
            tier="basic",
            question="Manual",
            answer_key={},
            grading_type="manual",
            explanation_link=None,
            created_at=datetime(2024, 1, 1),
        )
        mock_sfield.return_value = [auto, manual]
        r = client.get(f"/products/{PID}/missions")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["mission_id"] == MISSION_ID
        assert data[0]["options"] == ["A", "B"]
        assert data[0]["type"] == "multiple_choice"

    @patch("src.routers.products.select_by_field")
    @patch("src.routers.products.select_by_id")
    def test_invalid_options_returns_500(self, mock_sid, mock_sfield, client):
        mock_sid.return_value = _sample_product()
        bad = QuestMission(
            mission_id=MISSION_ID,
            product_id=PID,
            tier="basic",
            question="Q?",
            answer_key={"options": "not-list"},
            grading_type="auto",
            explanation_link=None,
            created_at=datetime(2024, 1, 1),
        )
        mock_sfield.return_value = [bad]
        r = client.get(f"/products/{PID}/missions")
        assert r.status_code == 500

    @patch("src.routers.products.select_by_id")
    def test_product_not_found_returns_404(self, mock_sid, client):
        mock_sid.return_value = None
        r = client.get(f"/products/{PID}/missions")
        assert r.status_code == 404


class TestGetClaimEvidence:
    @patch("src.routers.products.select_by_field")
    @patch("src.routers.products.select_by_id")
    def test_success_includes_rationale(self, mock_sid, mock_sfield, client):
        claim = _sample_claim()
        ev = _sample_evidence()
        mock_sid.return_value = claim
        mock_sfield.return_value = [ev]
        r = client.get(f"/products/{PID}/claims/{CLAIM_ID}/evidence")
        assert r.status_code == 200
        j = r.json()
        assert j["claim_id"] == CLAIM_ID
        assert j["rationale"] == "Pending review"
        assert len(j["evidence"]) == 1

    @patch("src.routers.products.select_by_id")
    def test_wrong_product_returns_404(self, mock_sid, client):
        c = _sample_claim()
        object.__setattr__(c, "product_id", "99999999-9999-9999-9999-999999999999")
        mock_sid.return_value = c
        r = client.get(f"/products/{PID}/claims/{CLAIM_ID}/evidence")
        assert r.status_code == 404

    def test_invalid_product_uuid_returns_400(self, client):
        r = client.get(f"/products/bad-uuid/claims/{CLAIM_ID}/evidence")
        assert r.status_code == 400
        assert "product_id" in r.json()["detail"]

    def test_invalid_claim_uuid_returns_400(self, client):
        r = client.get(f"/products/{PID}/claims/not-a-uuid/evidence")
        assert r.status_code == 400
        assert "claim_id" in r.json()["detail"]

    @patch("src.routers.products.select_by_id")
    def test_claim_not_found_returns_404(self, mock_sid, client):
        mock_sid.return_value = None
        r = client.get(f"/products/{PID}/claims/{CLAIM_ID}/evidence")
        assert r.status_code == 404


class TestVerifyClaim:
    @patch("src.routers.products.log_claim_change")
    @patch("src.routers.products.get_client")
    @patch("src.routers.products.select_by_field")
    @patch("src.routers.products.select_by_id")
    def test_verify_success(
        self, mock_sid, mock_sfield, mock_gclient, mock_log, verifier_client
    ):
        mock_sid.return_value = _sample_claim()
        mock_sfield.return_value = [_sample_evidence()]
        mock_gclient.return_value.table.return_value.update.return_value.eq.return_value.execute.return_value = None
        r = verifier_client.put(
            f"/products/{PID}/claims/{CLAIM_ID}/verify", params={"notes": "ok"}
        )
        assert r.status_code == 200
        assert r.json() == {"status": "verified"}
        mock_log.assert_called_once()

    @patch("src.routers.products.select_by_field")
    @patch("src.routers.products.select_by_id")
    def test_verify_no_evidence_returns_400(self, mock_sid, mock_sfield, verifier_client):
        mock_sid.return_value = _sample_claim()
        mock_sfield.return_value = []
        r = verifier_client.put(f"/products/{PID}/claims/{CLAIM_ID}/verify")
        assert r.status_code == 400

    @patch("src.routers.products.select_by_id")
    def test_verify_claim_not_found(self, mock_sid, verifier_client):
        mock_sid.return_value = None
        r = verifier_client.put(f"/products/{PID}/claims/{CLAIM_ID}/verify")
        assert r.status_code == 404

    def test_verify_invalid_product_uuid_returns_400(self, verifier_client):
        r = verifier_client.put(f"/products/bad/claims/{CLAIM_ID}/verify")
        assert r.status_code == 400
        assert "Invalid" in r.json()["detail"]

    def test_verify_invalid_claim_uuid_returns_400(self, verifier_client):
        r = verifier_client.put(f"/products/{PID}/claims/not-a-uuid/verify")
        assert r.status_code == 400
        assert "Invalid" in r.json()["detail"]


class TestUnverifyClaim:
    @patch("src.routers.products.log_claim_change")
    @patch("src.routers.products.get_client")
    @patch("src.routers.products.select_by_id")
    def test_unverify_success(self, mock_sid, mock_gclient, mock_log, verifier_client):
        mock_sid.return_value = _sample_claim(confidence="verified")
        mock_gclient.return_value.table.return_value.update.return_value.eq.return_value.execute.return_value = None
        r = verifier_client.put(f"/products/{PID}/claims/{CLAIM_ID}/unverify")
        assert r.status_code == 200
        assert r.json() == {"status": "unverified"}
        mock_log.assert_called_once()

    @patch("src.routers.products.select_by_id")
    def test_unverify_claim_not_found_returns_404(self, mock_sid, verifier_client):
        mock_sid.return_value = None
        r = verifier_client.put(f"/products/{PID}/claims/{CLAIM_ID}/unverify")
        assert r.status_code == 404

    def test_unverify_invalid_product_uuid_returns_400(self, verifier_client):
        r = verifier_client.put(f"/products/bad-uuid/claims/{CLAIM_ID}/unverify")
        assert r.status_code == 400

    def test_unverify_invalid_claim_uuid_returns_400(self, verifier_client):
        r = verifier_client.put(f"/products/{PID}/claims/bad-uuid/unverify")
        assert r.status_code == 400


class TestUpdateClaimConfidence:
    @patch("src.routers.products.log_claim_change")
    @patch("src.routers.products.get_client")
    @patch("src.routers.products.select_by_id")
    def test_updates_confidence(self, mock_sid, mock_gclient, mock_log, verifier_client):
        mock_sid.return_value = _sample_claim()
        mock_gclient.return_value.table.return_value.update.return_value.eq.return_value.execute.return_value = None
        r = verifier_client.put(
            f"/products/{PID}/claims/{CLAIM_ID}/confidence",
            params={"confidence_label": "partially_verified"},
        )
        assert r.status_code == 200
        assert r.json() == {"status": "updated"}
        mock_log.assert_called_once()

    @patch("src.routers.products.select_by_id")
    def test_confidence_claim_not_found_returns_404(self, mock_sid, verifier_client):
        mock_sid.return_value = None
        r = verifier_client.put(
            f"/products/{PID}/claims/{CLAIM_ID}/confidence",
            params={"confidence_label": "unverified"},
        )
        assert r.status_code == 404

    def test_confidence_missing_query_param_returns_422(self, verifier_client):
        r = verifier_client.put(f"/products/{PID}/claims/{CLAIM_ID}/confidence")
        assert r.status_code == 422

    def test_confidence_invalid_product_uuid_returns_400(self, verifier_client):
        r = verifier_client.put(
            f"/products/not-uuid/claims/{CLAIM_ID}/confidence",
            params={"confidence_label": "unverified"},
        )
        assert r.status_code == 400

    def test_confidence_invalid_claim_uuid_returns_400(self, verifier_client):
        r = verifier_client.put(
            f"/products/{PID}/claims/not-uuid/confidence",
            params={"confidence_label": "unverified"},
        )
        assert r.status_code == 400


class TestGetVerificationHistory:
    @patch("src.routers.products.get_client")
    def test_returns_changelog_rows(self, mock_gclient, verifier_client):
        mock_resp = MagicMock()
        mock_resp.data = [{"log_id": "1"}]
        mock_gclient.return_value.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = mock_resp
        r = verifier_client.get(f"/products/{PID}/claims/{CLAIM_ID}/history")
        assert r.status_code == 200
        assert r.json() == [{"log_id": "1"}]


class TestQuestMissionPublicModel:
    def test_roundtrip(self):
        m = QuestMissionPublic(
            mission_id=MISSION_ID,
            product_id=PID,
            tier="basic",
            question="Q",
            options=["a", "b"],
            created_at=datetime(2024, 1, 1),
        )
        d = m.model_dump()
        assert d["type"] == "multiple_choice"


class TestProductEvidenceViewModel:
    def test_build(self):
        g = ClaimEvidenceGroup(
            claim_id=CLAIM_ID,
            claim_type="t",
            claim_text="txt",
            confidence_label="unverified",
            evidence=[_sample_evidence()],
        )
        v = ProductEvidenceView(product_id=PID, groups=[g])
        assert len(v.groups) == 1


class TestCreateProduct:
    """Test suite for POST /products endpoint"""

    def setup_method(self):
        """Set up test dependencies."""
        self.valid_body = {
            "name": "Test Product",
            "category": "food",
            "brand": "Test Brand",
            "description": "A test product",
        }

    # patch replaces the function being called with a mock function
    @patch("src.routers.products.log_entity_change")
    @patch("src.routers.products.insert_one")
    def test_create_product_success(self, mock_insert, mock_log, verifier_client):
        """Test successful creation of a product."""
        mock_insert.return_value = {
            "product_id": "0000-0000-0000-0000",
            **self.valid_body,
        }  # ** allows this to add the dictionary to this one

        response = verifier_client.post("/products", json=self.valid_body)
        assert response.status_code == 201

        mock_insert.assert_called_once()
        assert mock_insert.call_args[0][0] == "Product"
        mock_log.assert_called_once()

    def test_create_product_missing_name(self, verifier_client):
        body = {"category": "food"}
        response = verifier_client.post("/products", json=body)
        assert response.status_code == 422

    def test_create_product_invalid_category(self, verifier_client):
        body = {"name": "Test", "category": "invalid_category"}
        response = verifier_client.post("/products", json=body)
        assert response.status_code == 422

    def test_create_product_no_auth(self, client):
        response = client.post("/products", json=self.valid_body)
        assert response.status_code in (401, 422)

    def test_create_product_non_verifier(self, client):
        # Override user_id but NOT require_verifier, should get 403
        app.dependency_overrides[get_current_user_id] = lambda: TEST_USER_ID
        # Return a consumer role, require_verifier should reject with 403
        app.dependency_overrides[get_current_user_role] = lambda: UserRole(
            role_id="role-00000000-0000-0000-0000-000000000002",
            user_id=TEST_USER_ID,
            role="consumer",
            created_at=datetime(2026, 1, 1),
        )
        response = client.post("/products", json=self.valid_body)
        app.dependency_overrides.clear()
        assert response.status_code == 403
