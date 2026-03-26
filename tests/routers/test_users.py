from datetime import datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.auth import get_current_user_id, get_current_user_role
from src.main import app
from src.models.user import QuestMission, UserProgress, UserRole
from src.routers.users import build_badges

USER_ID = "550e8400-e29b-41d4-a716-446655440000"


class TestGetMyRole:
    def setup_method(self):
        self.client = TestClient(app)
        self.user_id = USER_ID

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_returns_consumer_when_no_role_assignment_exists(self):
        # Users without a stored role should still resolve to consumer.
        async def override_user_id():
            return self.user_id

        async def override_user_role():
            return None

        app.dependency_overrides[get_current_user_id] = override_user_id
        app.dependency_overrides[get_current_user_role] = override_user_role

        response = self.client.get("/users/me/role")

        assert response.status_code == 200
        assert response.json() == {"user_id": self.user_id, "role": "consumer"}

    def test_returns_assigned_role_when_present(self):
        # Stored role assignments should be returned unchanged.
        async def override_user_id():
            return self.user_id

        async def override_user_role():
            return UserRole(
                role_id="660e8400-e29b-41d4-a716-446655440000",
                user_id=self.user_id,
                role="verifier",
                created_at=datetime.now(),
            )

        app.dependency_overrides[get_current_user_id] = override_user_id
        app.dependency_overrides[get_current_user_role] = override_user_role

        response = self.client.get("/users/me/role")

        assert response.status_code == 200
        assert response.json() == {"user_id": self.user_id, "role": "verifier"}


# ---------------------------------------------------------------------------
# build_badges
# ---------------------------------------------------------------------------

_ZERO_TIER = {"basic": 0, "intermediate": 0, "advanced": 0}
_ONE_OF_EACH = {"basic": 1, "intermediate": 1, "advanced": 1}


class TestBuildBadges:
    def _badge(self, badges, badge_id):
        return next(b for b in badges if b["id"] == badge_id)

    def test_no_progress_all_badges_unearned(self):
        badges = build_badges(0, _ZERO_TIER.copy(), _ONE_OF_EACH.copy())
        assert all(not b["earned"] for b in badges)

    def test_first_steps_earned_at_one_completion(self):
        badges = build_badges(1, {"basic": 1, "intermediate": 0, "advanced": 0}, _ONE_OF_EACH.copy())
        assert self._badge(badges, "first_steps")["earned"] is True

    def test_first_steps_not_earned_at_zero(self):
        badges = build_badges(0, _ZERO_TIER.copy(), _ONE_OF_EACH.copy())
        assert self._badge(badges, "first_steps")["earned"] is False

    def test_getting_going_earned_at_three(self):
        badges = build_badges(3, {"basic": 3, "intermediate": 0, "advanced": 0}, _ONE_OF_EACH.copy())
        assert self._badge(badges, "getting_going")["earned"] is True

    def test_explorer_earned_at_six(self):
        badges = build_badges(6, {"basic": 3, "intermediate": 2, "advanced": 1}, _ONE_OF_EACH.copy())
        assert self._badge(badges, "explorer")["earned"] is True

    def test_basic_complete_earned_when_all_basic_done(self):
        badges = build_badges(2, {"basic": 2, "intermediate": 0, "advanced": 0}, {"basic": 2, "intermediate": 1, "advanced": 1})
        assert self._badge(badges, "basic_complete")["earned"] is True

    def test_basic_complete_not_earned_when_count_is_zero(self):
        badges = build_badges(0, _ZERO_TIER.copy(), {"basic": 0, "intermediate": 1, "advanced": 1})
        assert self._badge(badges, "basic_complete")["earned"] is False

    def test_intermediate_complete_earned(self):
        badges = build_badges(1, {"basic": 0, "intermediate": 1, "advanced": 0}, {"basic": 1, "intermediate": 1, "advanced": 1})
        assert self._badge(badges, "intermediate_complete")["earned"] is True

    def test_advanced_complete_earned(self):
        badges = build_badges(1, {"basic": 0, "intermediate": 0, "advanced": 1}, {"basic": 1, "intermediate": 1, "advanced": 1})
        assert self._badge(badges, "advanced_complete")["earned"] is True

    def test_quest_master_earned_when_all_complete(self):
        badges = build_badges(3, {"basic": 1, "intermediate": 1, "advanced": 1}, {"basic": 1, "intermediate": 1, "advanced": 1})
        assert self._badge(badges, "quest_master")["earned"] is True

    def test_quest_master_not_earned_when_zero_total_missions(self):
        badges = build_badges(0, _ZERO_TIER.copy(), _ZERO_TIER.copy())
        assert self._badge(badges, "quest_master")["earned"] is False

    def test_progress_current_clamped_for_first_steps(self):
        badges = build_badges(5, {"basic": 5, "intermediate": 0, "advanced": 0}, _ONE_OF_EACH.copy())
        assert self._badge(badges, "first_steps")["progress_current"] == 1

    def test_returns_seven_badges(self):
        badges = build_badges(0, _ZERO_TIER.copy(), _ZERO_TIER.copy())
        assert len(badges) == 7


# ---------------------------------------------------------------------------
# GET /users/me/progress
# ---------------------------------------------------------------------------


def _make_mission(mission_id, tier="basic"):
    return QuestMission(
        mission_id=mission_id,
        tier=tier,
        question="Q?",
        grading_type="auto",
        created_at=datetime(2026, 1, 1),
    )


def _make_progress(mission_id, completed=False, score=0, attempts=1, completed_at=None):
    return UserProgress(
        user_id=USER_ID,
        mission_id=mission_id,
        completed=completed,
        score=score,
        attempts=attempts,
        completed_at=completed_at,
        created_at=datetime(2026, 1, 1),
    )


class TestGetMyProgress:
    def setup_method(self):
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        self.client = TestClient(app)

    def teardown_method(self):
        app.dependency_overrides.clear()

    @patch("src.routers.users.select_all")
    @patch("src.routers.users.select_by_field")
    def test_empty_progress_returns_zeroes(self, mock_select_field, mock_select_all):
        mock_select_field.return_value = []
        mock_select_all.return_value = []

        response = self.client.get("/users/me/progress")

        assert response.status_code == 200
        data = response.json()
        assert data["total_completed"] == 0
        assert data["total_points"] == 0
        assert data["missions"] == []
        assert data["recent_completions"] == []

    @patch("src.routers.users.select_all")
    @patch("src.routers.users.select_by_field")
    def test_completed_mission_counted(self, mock_select_field, mock_select_all):
        mission_id = "aaaaaaaa-0000-0000-0000-000000000001"
        mock_select_all.return_value = [_make_mission(mission_id, "basic")]
        mock_select_field.return_value = [
            _make_progress(mission_id, completed=True, score=10,
                           completed_at=datetime(2026, 3, 1, tzinfo=timezone.utc))
        ]

        response = self.client.get("/users/me/progress")

        data = response.json()
        assert data["total_completed"] == 1
        assert data["total_points"] == 10
        assert data["missions_completed_by_tier"]["basic"] == 1

    @patch("src.routers.users.select_all")
    @patch("src.routers.users.select_by_field")
    def test_incomplete_mission_not_counted_in_points(self, mock_select_field, mock_select_all):
        mission_id = "aaaaaaaa-0000-0000-0000-000000000002"
        mock_select_all.return_value = [_make_mission(mission_id, "intermediate")]
        mock_select_field.return_value = [
            _make_progress(mission_id, completed=False, score=0)
        ]

        response = self.client.get("/users/me/progress")

        data = response.json()
        assert data["total_completed"] == 0
        assert data["total_points"] == 0

    @patch("src.routers.users.select_all")
    @patch("src.routers.users.select_by_field")
    def test_progress_without_matching_mission_is_skipped(self, mock_select_field, mock_select_all):
        mock_select_all.return_value = []  # no missions in DB
        mock_select_field.return_value = [
            _make_progress("orphan-id", completed=True, score=10)
        ]

        response = self.client.get("/users/me/progress")

        data = response.json()
        assert data["total_completed"] == 0
        assert data["missions"] == []

    @patch("src.routers.users.select_all")
    @patch("src.routers.users.select_by_field")
    def test_recent_completions_sorted_newest_first(self, mock_select_field, mock_select_all):
        id1 = "aaaaaaaa-0000-0000-0000-000000000001"
        id2 = "aaaaaaaa-0000-0000-0000-000000000002"
        mock_select_all.return_value = [
            _make_mission(id1, "basic"),
            _make_mission(id2, "basic"),
        ]
        mock_select_field.return_value = [
            _make_progress(id1, completed=True, score=10,
                           completed_at=datetime(2026, 1, 1, tzinfo=timezone.utc)),
            _make_progress(id2, completed=True, score=10,
                           completed_at=datetime(2026, 3, 1, tzinfo=timezone.utc)),
        ]

        response = self.client.get("/users/me/progress")

        completions = response.json()["recent_completions"]
        assert len(completions) == 2
        assert completions[0]["mission_id"] == id2  # newer first

    @patch("src.routers.users.select_all")
    @patch("src.routers.users.select_by_field")
    def test_badges_included_in_response(self, mock_select_field, mock_select_all):
        mock_select_field.return_value = []
        mock_select_all.return_value = []

        response = self.client.get("/users/me/progress")

        assert "badges" in response.json()

    def test_unauthenticated_returns_401_or_422(self):
        app.dependency_overrides.clear()
        plain_client = TestClient(app)
        response = plain_client.get("/users/me/progress")
        assert response.status_code in (401, 422)
