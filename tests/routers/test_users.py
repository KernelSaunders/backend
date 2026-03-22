"""Tests for users router."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.auth import get_current_user_id, get_current_user_role
from src.main import app
from src.models.user import UserRole


class TestGetMyRoleEndpoint:
    """Test suite for GET /users/me/role."""

    def setup_method(self):
        self.client = TestClient(app)
        self.user_id = "00000000-0000-0000-0000-000000000111"

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_get_my_role_returns_consumer_when_no_role(self):
        app.dependency_overrides[get_current_user_id] = lambda: self.user_id
        app.dependency_overrides[get_current_user_role] = lambda: None

        response = self.client.get("/users/me/role")

        assert response.status_code == 200
        assert response.json() == {"user_id": self.user_id, "role": "consumer"}

    def test_get_my_role_returns_verifier_role(self):
        app.dependency_overrides[get_current_user_id] = lambda: self.user_id
        app.dependency_overrides[get_current_user_role] = lambda: UserRole(
            role_id="role-1",
            user_id=self.user_id,
            role="verifier",
            created_at=datetime(2026, 1, 1),
        )

        response = self.client.get("/users/me/role")

        assert response.status_code == 200
        assert response.json() == {"user_id": self.user_id, "role": "verifier"}

    def test_get_my_role_returns_maintainer_role(self):
        app.dependency_overrides[get_current_user_id] = lambda: self.user_id
        app.dependency_overrides[get_current_user_role] = lambda: UserRole(
            role_id="role-2",
            user_id=self.user_id,
            role="maintainer",
            created_at=datetime(2026, 1, 1),
        )

        response = self.client.get("/users/me/role")

        assert response.status_code == 200
        assert response.json() == {"user_id": self.user_id, "role": "maintainer"}

    def test_get_my_role_returns_consumer_role_from_db(self):
        app.dependency_overrides[get_current_user_id] = lambda: self.user_id
        app.dependency_overrides[get_current_user_role] = lambda: UserRole(
            role_id="role-3",
            user_id=self.user_id,
            role="consumer",
            created_at=datetime(2026, 1, 1),
        )

        response = self.client.get("/users/me/role")

        assert response.status_code == 200
        assert response.json() == {"user_id": self.user_id, "role": "consumer"}

    def test_get_my_role_uses_user_id_from_dependency(self):
        dep_user_id = "00000000-0000-0000-0000-00000000abcd"
        app.dependency_overrides[get_current_user_id] = lambda: dep_user_id
        app.dependency_overrides[get_current_user_role] = lambda: None

        response = self.client.get("/users/me/role")

        assert response.status_code == 200
        assert response.json()["user_id"] == dep_user_id

    def test_get_my_role_response_structure(self):
        app.dependency_overrides[get_current_user_id] = lambda: self.user_id
        app.dependency_overrides[get_current_user_role] = lambda: None

        response = self.client.get("/users/me/role")
        data = response.json()

        assert response.status_code == 200
        assert "user_id" in data
        assert "role" in data
        assert isinstance(data["user_id"], str)
        assert isinstance(data["role"], str)

    def test_get_my_role_without_auth_header_still_uses_dependency_result(self):
        app.dependency_overrides[get_current_user_id] = lambda: self.user_id
        app.dependency_overrides[get_current_user_role] = lambda: None

        response = self.client.get("/users/me/role", headers={})

        assert response.status_code == 200
        assert response.json() == {"user_id": self.user_id, "role": "consumer"}


class TestGetMyRoleAuthRequired:
    """GET /users/me/role without dependency overrides — real auth stack."""

    def setup_method(self):
        self.client = TestClient(app)

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_missing_authorization_header_returns_422(self):
        """FastAPI reports missing required Header as 422 validation error."""
        app.dependency_overrides.clear()
        response = self.client.get("/users/me/role")
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert any(
            err.get("loc") == ["header", "authorization"] and err.get("type") == "missing"
            for err in detail
        )

    def test_non_bearer_scheme_returns_401(self):
        app.dependency_overrides.clear()
        response = self.client.get(
            "/users/me/role",
            headers={"Authorization": "Token not-bearer"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid auth header"

    def test_invalid_bearer_token_returns_401(self):
        app.dependency_overrides.clear()
        mock_client = MagicMock()
        mock_client.auth.get_user.side_effect = Exception("invalid jwt")

        with patch("src.auth.get_client", return_value=mock_client):
            response = self.client.get(
                "/users/me/role",
                headers={"Authorization": "Bearer bad-token"},
            )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid token"
        mock_client.auth.get_user.assert_called_once_with("bad-token")
