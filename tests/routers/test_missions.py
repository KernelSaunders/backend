"""Tests for missions router."""

from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.auth import get_current_user_id
from src.main import app
from src.models.user import QuestMission, UserProgress
from src.routers.missions import (
    MissionAttemptIn,
    _norm_answer,
    create_attempt,
    mission_points,
    upsert_user_progress,
    validate_uuid,
)

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"


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
        self.mission_id = "550e8400-e29b-41d4-a716-446655440000"
        # Bypass JWT auth for all endpoint tests in this class
        app.dependency_overrides[get_current_user_id] = lambda: TEST_USER_ID
        # Prevent real DB writes; return None-valued progress so the response
        # only serialises 'correct' (exclude_none on the route drops the rest)
        self._upsert_patcher = patch("src.routers.missions.upsert_user_progress")
        mock_upsert = self._upsert_patcher.start()
        mock_upsert.return_value = (Mock(completed=None, attempts=None), None)
        self.client = TestClient(app)

    def teardown_method(self):
        app.dependency_overrides.clear()
        self._upsert_patcher.stop()

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

    @patch("src.routers.missions.upsert_user_progress")
    @patch("src.routers.missions.select_by_id")
    def test_create_attempt_direct_function_success(self, mock_select_by_id, mock_upsert):
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
        mock_upsert.return_value = (Mock(completed=True, attempts=1), 30)

        result = create_attempt(
            mission_id,
            attempt=MissionAttemptIn(option_index=1),
            user_id=TEST_USER_ID,
        )
        assert result.correct is True


# ---------------------------------------------------------------------------
# mission_points
# ---------------------------------------------------------------------------


class TestMissionPoints:
    def test_basic_returns_10(self):
        assert mission_points("basic") == 10

    def test_intermediate_returns_20(self):
        assert mission_points("intermediate") == 20

    def test_advanced_returns_30(self):
        assert mission_points("advanced") == 30

    def test_unknown_tier_returns_0(self):
        assert mission_points("unknown") == 0

    def test_empty_string_returns_0(self):
        assert mission_points("") == 0


# ---------------------------------------------------------------------------
# upsert_user_progress
# ---------------------------------------------------------------------------


def _make_mission(tier="basic"):
    return QuestMission(
        mission_id="550e8400-e29b-41d4-a716-446655440000",
        tier=tier,
        question="Test?",
        answer_key={"options": ["A", "B"], "correct": "A"},
        grading_type="auto",
        created_at=datetime(2026, 1, 1),
    )


def _make_progress(completed=False, attempts=None, completed_at=None, score=None):
    return UserProgress(
        user_id=TEST_USER_ID,
        mission_id="550e8400-e29b-41d4-a716-446655440000",
        completed=completed,
        attempts=attempts,
        score=score,
        completed_at=completed_at,
        created_at=datetime(2026, 1, 1),
    )


class TestUpsertUserProgress:
    @patch("src.routers.missions.get_client")
    @patch("src.routers.missions.select_by_field")
    def test_new_user_correct_answer_inserts_and_awards_points(
        self, mock_select, mock_get_client
    ):
        mock_select.return_value = []  # no existing progress
        inserted_row = _make_progress(completed=True, attempts=1, score=10)
        mock_get_client.return_value.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[inserted_row.model_dump()]
        )

        mission = _make_mission("basic")
        progress, points = upsert_user_progress(TEST_USER_ID, mission, correct=True)

        assert progress.completed is True
        assert points == 10

    @patch("src.routers.missions.get_client")
    @patch("src.routers.missions.select_by_field")
    def test_new_user_incorrect_answer_inserts_and_awards_zero_points(
        self, mock_select, mock_get_client
    ):
        mock_select.return_value = []
        inserted_row = _make_progress(completed=False, attempts=1, score=0)
        mock_get_client.return_value.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[inserted_row.model_dump()]
        )

        mission = _make_mission("basic")
        progress, points = upsert_user_progress(TEST_USER_ID, mission, correct=False)

        assert progress.completed is False
        assert points == 0

    @patch("src.routers.missions.get_client")
    @patch("src.routers.missions.select_by_field")
    def test_existing_user_first_correct_answer_awards_points(
        self, mock_select, mock_get_client
    ):
        existing = _make_progress(completed=False, attempts=2)
        mock_select.return_value = [existing]
        updated_row = _make_progress(completed=True, attempts=3, score=20)
        (
            mock_get_client.return_value.table.return_value.update.return_value
            .eq.return_value.eq.return_value.execute.return_value
        ) = MagicMock(data=[updated_row.model_dump()])

        mission = _make_mission("intermediate")
        progress, points = upsert_user_progress(TEST_USER_ID, mission, correct=True)

        assert points == 20

    @patch("src.routers.missions.get_client")
    @patch("src.routers.missions.select_by_field")
    def test_already_completed_correct_answer_awards_zero_points(
        self, mock_select, mock_get_client
    ):
        existing = _make_progress(
            completed=True, attempts=1, completed_at=datetime(2026, 1, 1)
        )
        mock_select.return_value = [existing]
        updated_row = _make_progress(completed=True, attempts=2, score=30)
        (
            mock_get_client.return_value.table.return_value.update.return_value
            .eq.return_value.eq.return_value.execute.return_value
        ) = MagicMock(data=[updated_row.model_dump()])

        mission = _make_mission("advanced")
        progress, points = upsert_user_progress(TEST_USER_ID, mission, correct=True)

        assert points == 0  # already completed, no double-awarding

    @patch("src.routers.missions.get_client")
    @patch("src.routers.missions.select_by_field")
    def test_existing_user_incorrect_answer_awards_zero_points(
        self, mock_select, mock_get_client
    ):
        existing = _make_progress(completed=False, attempts=1)
        mock_select.return_value = [existing]
        updated_row = _make_progress(completed=False, attempts=2, score=0)
        (
            mock_get_client.return_value.table.return_value.update.return_value
            .eq.return_value.eq.return_value.execute.return_value
        ) = MagicMock(data=[updated_row.model_dump()])

        mission = _make_mission("basic")
        progress, points = upsert_user_progress(TEST_USER_ID, mission, correct=False)

        assert points == 0

    @patch("src.routers.missions.get_client")
    @patch("src.routers.missions.select_by_field")
    def test_attempts_increments_on_each_call(self, mock_select, mock_get_client):
        existing = _make_progress(completed=False, attempts=4)
        mock_select.return_value = [existing]
        updated_row = _make_progress(completed=False, attempts=5, score=0)
        (
            mock_get_client.return_value.table.return_value.update.return_value
            .eq.return_value.eq.return_value.execute.return_value
        ) = MagicMock(data=[updated_row.model_dump()])

        mission = _make_mission("basic")
        progress, _ = upsert_user_progress(TEST_USER_ID, mission, correct=False)

        assert progress.attempts == 5
