# C:/backend/.venv/Scripts/python.exe -m pytest tests/routers/test_products.py::TestValidateUuid tests/routers/test_products.py::TestGetProduct --cov=src.routers.products --cov-report=term-missing

"""Tests for products router."""

from datetime import datetime
from unittest import mock
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from src.auth import get_current_user_id, get_current_user_role
from src.main import app
from src.models import Claim, Evidence, InputShare, Product, Stage
from src.models.user import UserRole
from src.routers.products import (
    ClaimWithEvidence,
    ProductTraceability,
    router,
    validate_uuid,
)

from tests.conftest import TEST_USER_ID


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
        """Set up test fixtures before each test method."""
        self.client = TestClient(app)

    def test_get_products_returns_list(self):
        """Test that GET /products returns a list of products."""
        # TODO: Implement test
        pass

    def test_get_products_empty_database(self):
        """Test GET /products when database is empty."""
        # TODO: Implement test
        pass

    def test_get_products_calls_select_all(self):
        """Test that get_products calls select_all with Product model."""
        # TODO: Implement test
        pass

    def test_get_products_response_status_code(self):
        """Test that GET /products returns 200 status code."""
        # TODO: Implement test
        pass

    def test_get_products_response_structure(self):
        """Test that GET /products returns correctly structured response."""
        # TODO: Implement test
        pass


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

    def test_get_product_response_status_code(self):
        """Test that GET /products/{id} returns 200 for valid product."""
        # TODO: Implement test
        pass

    def test_get_product_response_structure(self):
        """Test that GET /products/{id} returns correctly structured response."""
        # TODO: Implement test
        pass


class TestGetProductTraceability:
    """Test suite for GET /products/{product_id}/traceability endpoint."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.client = TestClient(app)

    def test_get_product_traceability_with_valid_id(self):
        """Test GET /products/{id}/traceability with valid product ID."""
        # TODO: Implement test
        pass

    def test_get_product_traceability_with_invalid_uuid(self):
        """Test that endpoint returns 400 for invalid UUID."""
        # TODO: Implement test
        pass

    def test_get_product_traceability_product_not_found(self):
        """Test that endpoint returns 404 when product not found."""
        # TODO: Implement test
        pass

    def test_get_product_traceability_includes_stages(self):
        """Test that response includes stages for the product."""
        # TODO: Implement test
        pass

    def test_get_product_traceability_stages_sorted_by_sequence(self):
        """Test that stages are sorted by sequence_order."""
        # TODO: Implement test
        pass

    def test_get_product_traceability_includes_input_shares(self):
        """Test that response includes input_shares for the product."""
        # TODO: Implement test
        pass

    def test_get_product_traceability_includes_claims_with_evidence(self):
        """Test that response includes claims with their evidence."""
        # TODO: Implement test
        pass

    def test_get_product_traceability_response_status_code(self):
        """Test that endpoint returns 200 for valid product."""
        # TODO: Implement test
        pass

    def test_get_product_traceability_response_structure(self):
        """Test that response follows ProductTraceability schema."""
        # TODO: Implement test
        pass

    def test_get_product_traceability_with_no_claims(self):
        """Test endpoint behavior when product has no claims."""
        # TODO: Implement test
        pass

    def test_get_product_traceability_with_no_stages(self):
        """Test endpoint behavior when product has no stages."""
        # TODO: Implement test
        pass

    def test_get_product_traceability_with_no_input_shares(self):
        """Test endpoint behavior when product has no input shares."""
        # TODO: Implement test
        pass


class TestClaimWithEvidence:
    """Test suite for ClaimWithEvidence model."""

    def test_claim_with_evidence_initialization(self):
        """Test ClaimWithEvidence model initialization."""
        # TODO: Implement test
        pass

    def test_claim_with_evidence_serialization(self):
        """Test ClaimWithEvidence serialization to dict."""
        # TODO: Implement test
        pass


class TestProductTraceability:
    """Test suite for ProductTraceability model."""

    def test_product_traceability_initialization(self):
        """Test ProductTraceability model initialization."""
        # TODO: Implement test
        pass

    def test_product_traceability_serialization(self):
        """Test ProductTraceability serialization to dict."""
        # TODO: Implement test
        pass


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
