"""Tests for Product model."""

import pytest
from datetime import datetime, date
from decimal import Decimal
from pydantic import ValidationError

from src.models.product import Product, Stage, InputShare


class TestProduct:
    """Test suite for Product model."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.valid_product_data = {
            "product_id": "test-product-id",
            "name": "Test Product",
            "category": "food",
            "brand": "Test Brand",
            "description": "Test product description",
            "image": "https://example.com/image.jpg",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

    def test_product_initialization_with_valid_data(self):
        """Test Product initialization with valid data."""
        product = Product(**self.valid_product_data)

        assert product.product_id == "test-product-id"
        assert product.name == "Test Product"
        assert product.category == "food"
        assert product.brand == "Test Brand"
        assert product.description == "Test product description"
        assert product.image == "https://example.com/image.jpg"
        assert isinstance(product.created_at, datetime)
        assert isinstance(product.updated_at, datetime)

    def test_product_initialization_with_minimal_required_fields(self):
        """Test Product initialization with only required fields."""
        minimal_data = {
            "product_id": "min-product",
            "name": "Minimal Product",
            "category": "other",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        product = Product(**minimal_data)

        assert product.product_id == "min-product"
        assert product.brand is None
        assert product.description is None
        assert product.image is None

    def test_product_category_validation(self):
        """Test that category accepts only valid literals."""
        valid_categories = ["food", "luxury", "supplements", "other"]

        for category in valid_categories:
            data = self.valid_product_data.copy()
            data["category"] = category
            product = Product(**data)
            assert product.category == category

    def test_product_category_invalid_value(self):
        """Test that invalid category raises ValidationError."""
        data = self.valid_product_data.copy()
        data["category"] = "invalid_category"

        with pytest.raises(ValidationError) as exc_info:
            Product(**data)

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("category",) for error in errors)

    def test_product_brand_optional(self):
        """Test that brand can be None."""
        data = self.valid_product_data.copy()
        data["brand"] = None
        product = Product(**data)

        assert product.brand is None

    def test_product_description_optional(self):
        """Test that description can be None."""
        data = self.valid_product_data.copy()
        data["description"] = None
        product = Product(**data)

        assert product.description is None

    def test_product_image_optional(self):
        """Test that image can be None."""
        data = self.valid_product_data.copy()
        data["image"] = None
        product = Product(**data)

        assert product.image is None

    def test_product_required_fields_missing(self):
        """Test that missing required fields raises ValidationError."""
        required_fields = ["product_id", "name", "category", "created_at", "updated_at"]

        for field in required_fields:
            data = self.valid_product_data.copy()
            del data[field]

            with pytest.raises(ValidationError) as exc_info:
                Product(**data)

            errors = exc_info.value.errors()
            assert any(error["loc"] == (field,) for error in errors)

    def test_product_serialization(self):
        """Test Product serialization to dict."""
        product = Product(**self.valid_product_data)
        product_dict = product.model_dump()

        assert isinstance(product_dict, dict)
        assert product_dict["product_id"] == "test-product-id"
        assert product_dict["name"] == "Test Product"
        assert product_dict["category"] == "food"

    def test_product_deserialization(self):
        """Test Product deserialization from dict."""
        product = Product(**self.valid_product_data)
        product_dict = product.model_dump()
        deserialized = Product(**product_dict)

        assert deserialized.product_id == product.product_id
        assert deserialized.name == product.name
        assert deserialized.category == product.category


class TestStage:
    """Test suite for Stage model."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.valid_stage_data = {
            "stage_id": "test-stage-id",
            "product_id": "test-product-id",
            "stage_type": "production",
            "location_country": "USA",
            "location_region": "California",
            "start_date": date(2024, 1, 1),
            "end_date": date(2024, 12, 31),
            "description": "Production stage",
            "sequence_order": 1,
            "created_at": datetime.now(),
        }

    def test_stage_initialization_with_valid_data(self):
        """Test Stage initialization with valid data."""
        stage = Stage(**self.valid_stage_data)

        assert stage.stage_id == "test-stage-id"
        assert stage.product_id == "test-product-id"
        assert stage.stage_type == "production"
        assert stage.location_country == "USA"
        assert stage.location_region == "California"
        assert stage.start_date == date(2024, 1, 1)
        assert stage.end_date == date(2024, 12, 31)
        assert stage.description == "Production stage"
        assert stage.sequence_order == 1
        assert isinstance(stage.created_at, datetime)

    def test_stage_initialization_with_minimal_required_fields(self):
        """Test Stage initialization with only required fields."""
        minimal_data = {
            "stage_id": "min-stage",
            "stage_type": "packaging",
        }
        stage = Stage(**minimal_data)

        assert stage.stage_id == "min-stage"
        assert stage.product_id is None
        assert stage.location_country is None
        assert stage.location_region is None
        assert stage.start_date is None
        assert stage.end_date is None
        assert stage.description is None
        assert stage.sequence_order is None
        assert stage.created_at is None

    def test_stage_product_id_optional(self):
        """Test that product_id can be None."""
        data = self.valid_stage_data.copy()
        data["product_id"] = None
        stage = Stage(**data)

        assert stage.product_id is None

    def test_stage_location_fields_optional(self):
        """Test that location_country and location_region can be None."""
        data = self.valid_stage_data.copy()
        data["location_country"] = None
        data["location_region"] = None
        stage = Stage(**data)

        assert stage.location_country is None
        assert stage.location_region is None

    def test_stage_date_fields_optional(self):
        """Test that start_date and end_date can be None."""
        data = self.valid_stage_data.copy()
        data["start_date"] = None
        data["end_date"] = None
        stage = Stage(**data)

        assert stage.start_date is None
        assert stage.end_date is None

    def test_stage_description_optional(self):
        """Test that description can be None."""
        data = self.valid_stage_data.copy()
        data["description"] = None
        stage = Stage(**data)

        assert stage.description is None

    def test_stage_sequence_order_optional(self):
        """Test that sequence_order can be None."""
        data = self.valid_stage_data.copy()
        data["sequence_order"] = None
        stage = Stage(**data)

        assert stage.sequence_order is None

    def test_stage_created_at_optional(self):
        """Test that created_at can be None."""
        data = self.valid_stage_data.copy()
        data["created_at"] = None
        stage = Stage(**data)

        assert stage.created_at is None

    def test_stage_required_fields_missing(self):
        """Test that missing required fields raises ValidationError."""
        required_fields = ["stage_id", "stage_type"]

        for field in required_fields:
            data = self.valid_stage_data.copy()
            del data[field]

            with pytest.raises(ValidationError) as exc_info:
                Stage(**data)

            errors = exc_info.value.errors()
            assert any(error["loc"] == (field,) for error in errors)

    def test_stage_serialization(self):
        """Test Stage serialization to dict."""
        stage = Stage(**self.valid_stage_data)
        stage_dict = stage.model_dump()

        assert isinstance(stage_dict, dict)
        assert stage_dict["stage_id"] == "test-stage-id"
        assert stage_dict["stage_type"] == "production"
        assert stage_dict["sequence_order"] == 1

    def test_stage_deserialization(self):
        """Test Stage deserialization from dict."""
        stage = Stage(**self.valid_stage_data)
        stage_dict = stage.model_dump()
        deserialized = Stage(**stage_dict)

        assert deserialized.stage_id == stage.stage_id
        assert deserialized.stage_type == stage.stage_type
        assert deserialized.location_country == stage.location_country


class TestInputShare:
    """Test suite for InputShare model."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.valid_input_share_data = {
            "input_id": "test-input-id",
            "product_id": "test-product-id",
            "input_name": "Test Input",
            "country": "USA",
            "percentage": Decimal("25.5"),
            "notes": "Test notes",
            "created_at": datetime.now(),
        }

    def test_input_share_initialization_with_valid_data(self):
        """Test InputShare initialization with valid data."""
        input_share = InputShare(**self.valid_input_share_data)

        assert input_share.input_id == "test-input-id"
        assert input_share.product_id == "test-product-id"
        assert input_share.input_name == "Test Input"
        assert input_share.country == "USA"
        assert input_share.percentage == Decimal("25.5")
        assert input_share.notes == "Test notes"
        assert isinstance(input_share.created_at, datetime)

    def test_input_share_initialization_with_minimal_required_fields(self):
        """Test InputShare initialization with only required fields."""
        minimal_data = {
            "input_id": "min-input",
            "input_name": "Minimal Input",
            "country": "Canada",
            "created_at": datetime.now(),
        }
        input_share = InputShare(**minimal_data)

        assert input_share.input_id == "min-input"
        assert input_share.product_id is None
        assert input_share.percentage is None
        assert input_share.notes is None

    def test_input_share_product_id_optional(self):
        """Test that product_id can be None."""
        data = self.valid_input_share_data.copy()
        data["product_id"] = None
        input_share = InputShare(**data)

        assert input_share.product_id is None

    def test_input_share_percentage_optional(self):
        """Test that percentage can be None."""
        data = self.valid_input_share_data.copy()
        data["percentage"] = None
        input_share = InputShare(**data)

        assert input_share.percentage is None

    def test_input_share_percentage_decimal_type(self):
        """Test that percentage is stored as Decimal type."""
        data = self.valid_input_share_data.copy()
        data["percentage"] = "50.75"  # Can be provided as string
        input_share = InputShare(**data)

        assert isinstance(input_share.percentage, Decimal)
        assert input_share.percentage == Decimal("50.75")

    def test_input_share_notes_optional(self):
        """Test that notes can be None."""
        data = self.valid_input_share_data.copy()
        data["notes"] = None
        input_share = InputShare(**data)

        assert input_share.notes is None

    def test_input_share_required_fields_missing(self):
        """Test that missing required fields raises ValidationError."""
        required_fields = ["input_id", "input_name", "country", "created_at"]

        for field in required_fields:
            data = self.valid_input_share_data.copy()
            del data[field]

            with pytest.raises(ValidationError) as exc_info:
                InputShare(**data)

            errors = exc_info.value.errors()
            assert any(error["loc"] == (field,) for error in errors)

    def test_input_share_serialization(self):
        """Test InputShare serialization to dict."""
        input_share = InputShare(**self.valid_input_share_data)
        share_dict = input_share.model_dump()

        assert isinstance(share_dict, dict)
        assert share_dict["input_id"] == "test-input-id"
        assert share_dict["input_name"] == "Test Input"
        assert share_dict["country"] == "USA"

    def test_input_share_deserialization(self):
        """Test InputShare deserialization from dict."""
        input_share = InputShare(**self.valid_input_share_data)
        share_dict = input_share.model_dump()
        deserialized = InputShare(**share_dict)

        assert deserialized.input_id == input_share.input_id
        assert deserialized.input_name == input_share.input_name
        assert deserialized.country == input_share.country
        assert deserialized.percentage == input_share.percentage
