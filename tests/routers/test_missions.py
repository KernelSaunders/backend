"""Tests for missions router."""

from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.main import app
from src.models.user import QuestMission
from src.routers.missions import (
    MissionAttemptIn,
    _norm_answer,
    create_attempt,
    validate_uuid,
)


class TestValidateUuid:
    """Test suite for validate_uuid utility."""

    def test_validate_uuid_returns_value_for_valid_uuid(self):
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        assert validate_uuid(valid_uuid, "mission_id") == valid_uuid

    def test_validate_uuid_raises_for_invalid_uuid(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_uuid("not-a-uuid", "mission_id")
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid mission_id format"


class TestNormAnswer:
    """Test suite for answer normalization helper."""

    def test_norm_answer_trims_whitespace(self):
        assert _norm_answer("  Verified Claim  ") == "verified claim"

    def test_norm_answer_casefolds_for_case_insensitive_compare(self):
        assert _norm_answer("VeRiFiEd") == "verified"


class TestCreateAttemptEndpoint:
    """Test suite for POST /missions/{mission_id}/attempts."""

    def setup_method(self):
        self.client = TestClient(app)
        self.mission_id = "550e8400-e29b-41d4-a716-446655440000"

    def _build_mission(self, answer_key=None):
        return QuestMission(
            mission_id=self.mission_id,
            product_id="11111111-2222-3333-4444-555555555555",
            tier="basic",
            question="Where was this made?",
            answer_key=answer_key,
            grading_type="auto",
            explanation_link=None,
            created_at=datetime(2026, 1, 1, 0, 0, 0),
        )

    @patch("src.routers.missions.select_by_id")
    def test_create_attempt_returns_correct_true(self, mock_select_by_id):
        mock_select_by_id.return_value = self._build_mission(
            {"options": ["USA", "France"], "correct": "USA"}
        )

        response = self.client.post(
            f"/missions/{self.mission_id}/attempts", json={"option_index": 0}
        )

        assert response.status_code == 200
        assert response.json() == {"correct": True}
        mock_select_by_id.assert_called_once_with(
            QuestMission, "mission_id", self.mission_id
        )

    @patch("src.routers.missions.select_by_id")
    def test_create_attempt_returns_correct_false(self, mock_select_by_id):
        mock_select_by_id.return_value = self._build_mission(
            {"options": ["USA", "France"], "correct": "USA"}
        )

        response = self.client.post(
            f"/missions/{self.mission_id}/attempts", json={"option_index": 1}
        )

        assert response.status_code == 200
        assert response.json() == {"correct": False}

    @patch("src.routers.missions.select_by_id")
    def test_create_attempt_compares_normalized_answers(self, mock_select_by_id):
        mock_select_by_id.return_value = self._build_mission(
            {"options": ["  usa  ", "France"], "correct": "USA"}
        )

        response = self.client.post(
            f"/missions/{self.mission_id}/attempts", json={"option_index": 0}
        )

        assert response.status_code == 200
        assert response.json() == {"correct": True}

    @patch("src.routers.missions.select_by_id")
    def test_create_attempt_returns_404_when_mission_not_found(self, mock_select_by_id):
        mock_select_by_id.return_value = None

        response = self.client.post(
            f"/missions/{self.mission_id}/attempts", json={"option_index": 0}
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Mission not found"

    def test_create_attempt_returns_400_for_invalid_mission_uuid(self):
        response = self.client.post(
            "/missions/invalid-uuid/attempts", json={"option_index": 0}
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid mission_id format"

    @patch("src.routers.missions.select_by_id")
    def test_create_attempt_returns_500_when_options_not_list(self, mock_select_by_id):
        mock_select_by_id.return_value = self._build_mission(
            {"options": "not-a-list", "correct": "USA"}
        )

        response = self.client.post(
            f"/missions/{self.mission_id}/attempts", json={"option_index": 0}
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "Mission is not attemptable (invalid options)"

    @patch("src.routers.missions.select_by_id")
    def test_create_attempt_returns_500_when_options_contains_non_string(
        self, mock_select_by_id
    ):
        mock_select_by_id.return_value = self._build_mission(
            {"options": ["USA", 2], "correct": "USA"}
        )

        response = self.client.post(
            f"/missions/{self.mission_id}/attempts", json={"option_index": 0}
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "Mission is not attemptable (invalid options)"

    @patch("src.routers.missions.select_by_id")
    def test_create_attempt_returns_500_when_correct_is_not_string(
        self, mock_select_by_id
    ):
        mock_select_by_id.return_value = self._build_mission(
            {"options": ["USA", "France"], "correct": 1}
        )

        response = self.client.post(
            f"/missions/{self.mission_id}/attempts", json={"option_index": 0}
        )

        assert response.status_code == 500
        assert (
            response.json()["detail"]
            == "Mission is not attemptable (invalid correct answer)"
        )

    @patch("src.routers.missions.select_by_id")
    def test_create_attempt_returns_422_for_negative_option_index(
        self, mock_select_by_id
    ):
        mock_select_by_id.return_value = self._build_mission(
            {"options": ["USA", "France"], "correct": "USA"}
        )

        response = self.client.post(
            f"/missions/{self.mission_id}/attempts", json={"option_index": -1}
        )

        assert response.status_code == 422
        assert response.json()["detail"] == "option_index out of range"

    @patch("src.routers.missions.select_by_id")
    def test_create_attempt_returns_422_for_out_of_range_option_index(
        self, mock_select_by_id
    ):
        mock_select_by_id.return_value = self._build_mission(
            {"options": ["USA", "France"], "correct": "USA"}
        )

        response = self.client.post(
            f"/missions/{self.mission_id}/attempts", json={"option_index": 2}
        )

        assert response.status_code == 422
        assert response.json()["detail"] == "option_index out of range"

    @patch("src.routers.missions.select_by_id")
    def test_create_attempt_returns_422_when_option_index_missing(
        self, mock_select_by_id
    ):
        mock_select_by_id.return_value = self._build_mission(
            {"options": ["USA", "France"], "correct": "USA"}
        )

        response = self.client.post(f"/missions/{self.mission_id}/attempts", json={})

        assert response.status_code == 422
        assert "option_index" in str(response.json())


class TestCreateAttemptUnit:
    """Unit-level direct call tests for create_attempt."""

    @patch("src.routers.missions.select_by_id")
    def test_create_attempt_direct_function_success(self, mock_select_by_id):
        mission_id = "550e8400-e29b-41d4-a716-446655440000"
        mission = QuestMission(
            mission_id=mission_id,
            tier="advanced",
            question="Test question",
            answer_key={"options": ["A", "B"], "correct": "B"},
            grading_type="auto",
            created_at=datetime(2026, 1, 1, 0, 0, 0),
        )
        mock_select_by_id.return_value = mission

        result = create_attempt(mission_id, attempt=MissionAttemptIn(option_index=1))
        assert result.correct is True
