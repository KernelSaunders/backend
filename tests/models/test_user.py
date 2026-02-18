"""Tests for User model."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.models.user import QuestMission, UserProgress, UserRole


class TestQuestMission:
    """Test suite for QuestMission model."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.valid_quest_mission_data = {
            "mission_id": "test-mission-id",
            "product_id": "test-product-id",
            "tier": "basic",
            "question": "What is the origin of this product?",
            "answer_key": {"correct_answer": "USA"},
            "grading_type": "auto",
            "explanation_link": "https://example.com/explanation",
            "created_at": datetime.now(),
        }

    def test_quest_mission_initialization_with_valid_data(self):
        """Test QuestMission initialization with valid data."""
        mission = QuestMission(**self.valid_quest_mission_data)

        assert mission.mission_id == "test-mission-id"
        assert mission.product_id == "test-product-id"
        assert mission.tier == "basic"
        assert mission.question == "What is the origin of this product?"
        assert mission.answer_key == {"correct_answer": "USA"}
        assert mission.grading_type == "auto"
        assert mission.explanation_link == "https://example.com/explanation"
        assert isinstance(mission.created_at, datetime)

    def test_quest_mission_initialization_with_minimal_required_fields(self):
        """Test QuestMission initialization with only required fields."""
        minimal_data = {
            "mission_id": "min-mission",
            "tier": "intermediate",
            "question": "Minimal question?",
            "grading_type": "manual",
            "created_at": datetime.now(),
        }
        mission = QuestMission(**minimal_data)

        assert mission.mission_id == "min-mission"
        assert mission.product_id is None
        assert mission.answer_key is None
        assert mission.explanation_link is None

    def test_quest_mission_tier_validation(self):
        """Test that tier accepts only valid literals."""
        valid_tiers = ["basic", "intermediate", "advanced"]

        for tier in valid_tiers:
            data = self.valid_quest_mission_data.copy()
            data["tier"] = tier
            mission = QuestMission(**data)
            assert mission.tier == tier

    def test_quest_mission_tier_invalid_value(self):
        """Test that invalid tier raises ValidationError."""
        data = self.valid_quest_mission_data.copy()
        data["tier"] = "expert"

        with pytest.raises(ValidationError) as exc_info:
            QuestMission(**data)

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("tier",) for error in errors)

    def test_quest_mission_grading_type_validation(self):
        """Test that grading_type accepts only valid literals."""
        valid_types = ["auto", "manual"]

        for grading_type in valid_types:
            data = self.valid_quest_mission_data.copy()
            data["grading_type"] = grading_type
            mission = QuestMission(**data)
            assert mission.grading_type == grading_type

    def test_quest_mission_grading_type_invalid_value(self):
        """Test that invalid grading_type raises ValidationError."""
        data = self.valid_quest_mission_data.copy()
        data["grading_type"] = "semi_auto"

        with pytest.raises(ValidationError) as exc_info:
            QuestMission(**data)

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("grading_type",) for error in errors)

    def test_quest_mission_product_id_optional(self):
        """Test that product_id can be None."""
        data = self.valid_quest_mission_data.copy()
        data["product_id"] = None
        mission = QuestMission(**data)

        assert mission.product_id is None

    def test_quest_mission_answer_key_optional(self):
        """Test that answer_key can be None."""
        data = self.valid_quest_mission_data.copy()
        data["answer_key"] = None
        mission = QuestMission(**data)

        assert mission.answer_key is None

    def test_quest_mission_explanation_link_optional(self):
        """Test that explanation_link can be None."""
        data = self.valid_quest_mission_data.copy()
        data["explanation_link"] = None
        mission = QuestMission(**data)

        assert mission.explanation_link is None

    def test_quest_mission_required_fields_missing(self):
        """Test that missing required fields raises ValidationError."""
        required_fields = [
            "mission_id",
            "tier",
            "question",
            "grading_type",
            "created_at",
        ]

        for field in required_fields:
            data = self.valid_quest_mission_data.copy()
            del data[field]

            with pytest.raises(ValidationError) as exc_info:
                QuestMission(**data)

            errors = exc_info.value.errors()
            assert any(error["loc"] == (field,) for error in errors)

    def test_quest_mission_serialization(self):
        """Test QuestMission serialization to dict."""
        mission = QuestMission(**self.valid_quest_mission_data)
        mission_dict = mission.model_dump()

        assert isinstance(mission_dict, dict)
        assert mission_dict["mission_id"] == "test-mission-id"
        assert mission_dict["tier"] == "basic"
        assert mission_dict["grading_type"] == "auto"
        assert mission_dict["answer_key"] == {"correct_answer": "USA"}

    def test_quest_mission_deserialization(self):
        """Test QuestMission deserialization from dict."""
        mission = QuestMission(**self.valid_quest_mission_data)
        mission_dict = mission.model_dump()
        deserialized = QuestMission(**mission_dict)

        assert deserialized.mission_id == mission.mission_id
        assert deserialized.tier == mission.tier
        assert deserialized.question == mission.question
        assert deserialized.answer_key == mission.answer_key


class TestUserProgress:
    """Test suite for UserProgress model."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.valid_user_progress_data = {
            "user_id": "test-user-id",
            "mission_id": "test-mission-id",
            "completed": True,
            "score": 100,
            "attempts": 1,
            "completed_at": datetime.now(),
            "created_at": datetime.now(),
        }

    def test_user_progress_initialization_with_valid_data(self):
        """Test UserProgress initialization with valid data."""
        progress = UserProgress(**self.valid_user_progress_data)

        assert progress.user_id == "test-user-id"
        assert progress.mission_id == "test-mission-id"
        assert progress.completed is True
        assert progress.score == 100
        assert progress.attempts == 1
        assert isinstance(progress.completed_at, datetime)
        assert isinstance(progress.created_at, datetime)

    def test_user_progress_initialization_with_minimal_required_fields(self):
        """Test UserProgress initialization with only required fields."""
        minimal_data = {
            "user_id": "min-user",
            "mission_id": "min-mission",
            "created_at": datetime.now(),
        }
        progress = UserProgress(**minimal_data)

        assert progress.user_id == "min-user"
        assert progress.completed is False  # Default value
        assert progress.score is None
        assert progress.attempts is None
        assert progress.completed_at is None

    def test_user_progress_completed_default_value(self):
        """Test that completed defaults to False."""
        data = {
            "user_id": "user-123",
            "mission_id": "mission-456",
            "created_at": datetime.now(),
        }
        progress = UserProgress(**data)

        assert progress.completed is False

    def test_user_progress_score_optional(self):
        """Test that score can be None."""
        data = self.valid_user_progress_data.copy()
        data["score"] = None
        progress = UserProgress(**data)

        assert progress.score is None

    def test_user_progress_attempts_optional(self):
        """Test that attempts can be None."""
        data = self.valid_user_progress_data.copy()
        data["attempts"] = None
        progress = UserProgress(**data)

        assert progress.attempts is None

    def test_user_progress_completed_at_optional(self):
        """Test that completed_at can be None."""
        data = self.valid_user_progress_data.copy()
        data["completed_at"] = None
        progress = UserProgress(**data)

        assert progress.completed_at is None

    def test_user_progress_required_fields_missing(self):
        """Test that missing required fields raises ValidationError."""
        required_fields = ["user_id", "mission_id", "created_at"]

        for field in required_fields:
            data = self.valid_user_progress_data.copy()
            del data[field]

            with pytest.raises(ValidationError) as exc_info:
                UserProgress(**data)

            errors = exc_info.value.errors()
            assert any(error["loc"] == (field,) for error in errors)

    def test_user_progress_serialization(self):
        """Test UserProgress serialization to dict."""
        progress = UserProgress(**self.valid_user_progress_data)
        progress_dict = progress.model_dump()

        assert isinstance(progress_dict, dict)
        assert progress_dict["user_id"] == "test-user-id"
        assert progress_dict["completed"] is True
        assert progress_dict["score"] == 100

    def test_user_progress_deserialization(self):
        """Test UserProgress deserialization from dict."""
        progress = UserProgress(**self.valid_user_progress_data)
        progress_dict = progress.model_dump()
        deserialized = UserProgress(**progress_dict)

        assert deserialized.user_id == progress.user_id
        assert deserialized.mission_id == progress.mission_id
        assert deserialized.completed == progress.completed
        assert deserialized.score == progress.score


class TestUserRole:
    """Test suite for UserRole model."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.valid_user_role_data = {
            "role_id": "test-role-id",
            "user_id": "test-user-id",
            "role": "consumer",
            "created_at": datetime.now(),
        }

    def test_user_role_initialization_with_valid_data(self):
        """Test UserRole initialization with valid data."""
        user_role = UserRole(**self.valid_user_role_data)

        assert user_role.role_id == "test-role-id"
        assert user_role.user_id == "test-user-id"
        assert user_role.role == "consumer"
        assert isinstance(user_role.created_at, datetime)

    def test_user_role_initialization_with_minimal_required_fields(self):
        """Test UserRole initialization with only required fields."""
        minimal_data = {
            "role_id": "min-role",
            "created_at": datetime.now(),
        }
        user_role = UserRole(**minimal_data)

        assert user_role.role_id == "min-role"
        assert user_role.user_id is None
        assert user_role.role is None

    def test_user_role_role_validation(self):
        """Test that role accepts only valid literals."""
        valid_roles = ["consumer", "verifier", "maintainer"]

        for role in valid_roles:
            data = self.valid_user_role_data.copy()
            data["role"] = role
            user_role = UserRole(**data)
            assert user_role.role == role

    def test_user_role_role_invalid_value(self):
        """Test that invalid role raises ValidationError."""
        data = self.valid_user_role_data.copy()
        data["role"] = "administrator"

        with pytest.raises(ValidationError) as exc_info:
            UserRole(**data)

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("role",) for error in errors)

    def test_user_role_user_id_optional(self):
        """Test that user_id can be None."""
        data = self.valid_user_role_data.copy()
        data["user_id"] = None
        user_role = UserRole(**data)

        assert user_role.user_id is None

    def test_user_role_role_optional(self):
        """Test that role can be None."""
        data = self.valid_user_role_data.copy()
        data["role"] = None
        user_role = UserRole(**data)

        assert user_role.role is None

    def test_user_role_required_fields_missing(self):
        """Test that missing required fields raises ValidationError."""
        required_fields = ["role_id", "created_at"]

        for field in required_fields:
            data = self.valid_user_role_data.copy()
            del data[field]

            with pytest.raises(ValidationError) as exc_info:
                UserRole(**data)

            errors = exc_info.value.errors()
            assert any(error["loc"] == (field,) for error in errors)

    def test_user_role_serialization(self):
        """Test UserRole serialization to dict."""
        user_role = UserRole(**self.valid_user_role_data)
        role_dict = user_role.model_dump()

        assert isinstance(role_dict, dict)
        assert role_dict["role_id"] == "test-role-id"
        assert role_dict["user_id"] == "test-user-id"
        assert role_dict["role"] == "consumer"

    def test_user_role_deserialization(self):
        """Test UserRole deserialization from dict."""
        user_role = UserRole(**self.valid_user_role_data)
        role_dict = user_role.model_dump()
        deserialized = UserRole(**role_dict)

        assert deserialized.role_id == user_role.role_id
        assert deserialized.user_id == user_role.user_id
        assert deserialized.role == user_role.role
