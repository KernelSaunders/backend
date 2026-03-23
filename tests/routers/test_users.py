from datetime import datetime

from fastapi.testclient import TestClient

from src.auth import get_current_user_id, get_current_user_role
from src.main import app
from src.models.user import UserRole


class TestGetMyRole:
    def setup_method(self):
        # Reuse the main app so this covers the real route behaviour.
        self.client = TestClient(app)
        self.user_id = "550e8400-e29b-41d4-a716-446655440000"

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
