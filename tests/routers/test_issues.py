"""Tests for issues router."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.auth import get_current_user_id, require_verifier
from src.main import app
from src.models.issue import IssueReports
from src.models.user import UserRole
from src.routers.issues import get_optional_user_id


class TestGetOptionalUserId:
    """Test suite for optional auth helper."""

    @pytest.mark.asyncio
    async def test_get_optional_user_id_returns_none_without_header(self):
        result = await get_optional_user_id()
        assert result is None

    @pytest.mark.asyncio
    async def test_get_optional_user_id_returns_none_with_non_bearer_header(self):
        result = await get_optional_user_id("Token abc123")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_optional_user_id_returns_user_id_for_valid_token(self):
        mock_user = MagicMock()
        mock_user.id = "00000000-0000-0000-0000-000000000001"
        mock_response = MagicMock()
        mock_response.user = mock_user

        mock_client = MagicMock()
        mock_client.auth.get_user.return_value = mock_response

        with patch("src.database.get_client", return_value=mock_client):
            result = await get_optional_user_id("Bearer valid-token")

        assert result == "00000000-0000-0000-0000-000000000001"
        mock_client.auth.get_user.assert_called_once_with("valid-token")

    @pytest.mark.asyncio
    async def test_get_optional_user_id_returns_none_when_user_missing(self):
        mock_response = MagicMock()
        mock_response.user = None
        mock_client = MagicMock()
        mock_client.auth.get_user.return_value = mock_response

        with patch("src.database.get_client", return_value=mock_client):
            result = await get_optional_user_id("Bearer valid-token")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_optional_user_id_returns_none_on_supabase_error(self):
        mock_client = MagicMock()
        mock_client.auth.get_user.side_effect = Exception("auth failure")

        with patch("src.database.get_client", return_value=mock_client):
            result = await get_optional_user_id("Bearer invalid-token")

        assert result is None


class TestCreateIssueEndpoint:
    """Test suite for POST /issues."""

    def setup_method(self):
        self.client = TestClient(app)
        self.body = {
            "product_id": "550e8400-e29b-41d4-a716-446655440000",
            "type": "other",
            "description": "Something is off",
        }

    def teardown_method(self):
        app.dependency_overrides.clear()

    @patch("src.routers.issues.insert_one")
    def test_create_issue_anonymous(self, mock_insert_one):
        mock_insert_one.return_value = {
            "issue_id": "id-1",
            **self.body,
            "status": "open",
            "created_at": datetime(2026, 1, 1).isoformat(),
            "updated_at": datetime(2026, 1, 1).isoformat(),
        }

        app.dependency_overrides[get_optional_user_id] = lambda: None
        response = self.client.post("/issues", json=self.body)

        assert response.status_code == 201
        assert response.json()["status"] == "open"
        record = mock_insert_one.call_args[0][1]
        assert record["product_id"] == self.body["product_id"]
        assert record["type"] == self.body["type"]
        assert record["description"] == self.body["description"]
        assert "reported_by" not in record

    @patch("src.routers.issues.insert_one")
    def test_create_issue_with_authenticated_user(self, mock_insert_one):
        mock_insert_one.return_value = {
            "issue_id": "id-2",
            **self.body,
            "reported_by": "00000000-0000-0000-0000-000000000111",
            "status": "open",
            "created_at": datetime(2026, 1, 1).isoformat(),
            "updated_at": datetime(2026, 1, 1).isoformat(),
        }

        app.dependency_overrides[get_optional_user_id] = (
            lambda: "00000000-0000-0000-0000-000000000111"
        )
        response = self.client.post("/issues", json=self.body)

        assert response.status_code == 201
        assert response.json()["reported_by"] == "00000000-0000-0000-0000-000000000111"
        record = mock_insert_one.call_args[0][1]
        assert record["reported_by"] == "00000000-0000-0000-0000-000000000111"

    def test_create_issue_invalid_body_returns_422(self):
        response = self.client.post("/issues", json={"type": "other"})
        assert response.status_code == 422


class TestListIssuesEndpoint:
    """Test suite for GET /issues."""

    def setup_method(self):
        self.client = TestClient(app)
        self.verifier_user_id = "00000000-0000-0000-0000-000000000111"
        app.dependency_overrides[get_current_user_id] = lambda: self.verifier_user_id
        app.dependency_overrides[require_verifier] = lambda: UserRole(
            role_id="role-1",
            user_id=self.verifier_user_id,
            role="verifier",
            created_at=datetime(2026, 1, 1),
        )

    def teardown_method(self):
        app.dependency_overrides.clear()

    @patch("src.routers.issues.get_client")
    def test_list_issues_returns_data(self, mock_get_client):
        mock_response = MagicMock()
        mock_response.data = [{"issue_id": "id-1", "status": "open"}]
        mock_query = MagicMock()
        mock_query.order.return_value.execute.return_value = mock_response
        mock_get_client.return_value.table.return_value.select.return_value = mock_query

        response = self.client.get("/issues")

        assert response.status_code == 200
        assert response.json() == [{"issue_id": "id-1", "status": "open"}]

    @patch("src.routers.issues.get_client")
    def test_list_issues_filters_by_status(self, mock_get_client):
        mock_response = MagicMock()
        mock_response.data = []
        mock_query = MagicMock()
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value.execute.return_value = mock_response
        mock_get_client.return_value.table.return_value.select.return_value = mock_query

        response = self.client.get("/issues?status=open")

        assert response.status_code == 200
        mock_query.eq.assert_any_call("status", "open")

    @patch("src.routers.issues.get_client")
    def test_list_issues_filters_by_product_id(self, mock_get_client):
        mock_response = MagicMock()
        mock_response.data = []
        mock_query = MagicMock()
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value.execute.return_value = mock_response
        mock_get_client.return_value.table.return_value.select.return_value = mock_query

        product_id = "550e8400-e29b-41d4-a716-446655440000"
        response = self.client.get(f"/issues?product_id={product_id}")

        assert response.status_code == 200
        mock_query.eq.assert_any_call("product_id", product_id)

    @patch("src.routers.issues.get_client")
    def test_list_issues_applies_both_filters(self, mock_get_client):
        mock_response = MagicMock()
        mock_response.data = []
        mock_query = MagicMock()
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value.execute.return_value = mock_response
        mock_get_client.return_value.table.return_value.select.return_value = mock_query

        product_id = "550e8400-e29b-41d4-a716-446655440000"
        response = self.client.get(f"/issues?status=open&product_id={product_id}")

        assert response.status_code == 200
        mock_query.eq.assert_any_call("status", "open")
        mock_query.eq.assert_any_call("product_id", product_id)

    def test_list_issues_forbidden_for_non_verifier(self):
        app.dependency_overrides[get_current_user_id] = lambda: self.verifier_user_id

        def _deny():
            from fastapi import HTTPException

            raise HTTPException(status_code=403, detail="Access forbidden")

        app.dependency_overrides[require_verifier] = _deny
        response = self.client.get("/issues")
        assert response.status_code == 403


class TestUpdateIssueEndpoint:
    """Test suite for PUT /issues/{issue_id}."""

    def setup_method(self):
        self.client = TestClient(app)
        self.verifier_user_id = "00000000-0000-0000-0000-000000000111"
        app.dependency_overrides[get_current_user_id] = lambda: self.verifier_user_id
        app.dependency_overrides[require_verifier] = lambda: UserRole(
            role_id="role-1",
            user_id=self.verifier_user_id,
            role="verifier",
            created_at=datetime(2026, 1, 1),
        )
        self.issue_id = "550e8400-e29b-41d4-a716-446655440000"

    def teardown_method(self):
        app.dependency_overrides.clear()

    @patch("src.routers.issues.log_entity_change")
    @patch("src.routers.issues.update_by_id")
    @patch("src.routers.issues.select_by_id")
    def test_update_issue_success(
        self, mock_select_by_id, mock_update_by_id, mock_log_entity_change
    ):
        mock_select_by_id.return_value = IssueReports(
            issue_id=self.issue_id,
            product_id="pid-1",
            reported_by=None,
            type="other",
            description="Old",
            status="open",
            resolution_note=None,
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 1, 1),
        )
        mock_update_by_id.return_value = {
            "issue_id": self.issue_id,
            "status": "resolved",
            "resolution_note": "done",
        }

        response = self.client.put(
            f"/issues/{self.issue_id}",
            json={"status": "resolved", "resolution_note": "done"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "resolved"
        mock_update_by_id.assert_called_once()
        mock_log_entity_change.assert_called_once()

    @patch("src.routers.issues.select_by_id")
    def test_update_issue_not_found(self, mock_select_by_id):
        mock_select_by_id.return_value = None

        response = self.client.put(f"/issues/{self.issue_id}", json={"status": "resolved"})

        assert response.status_code == 404
        assert response.json()["detail"] == "Issue not found"

    @patch("src.routers.issues.log_entity_change")
    @patch("src.routers.issues.update_by_id")
    @patch("src.routers.issues.select_by_id")
    def test_update_issue_without_resolution_note(
        self, mock_select_by_id, mock_update_by_id, mock_log_entity_change
    ):
        mock_select_by_id.return_value = IssueReports(
            issue_id=self.issue_id,
            product_id="pid-1",
            reported_by=None,
            type="other",
            description="Old",
            status="open",
            resolution_note=None,
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 1, 1),
        )
        mock_update_by_id.return_value = {"issue_id": self.issue_id, "status": "under_review"}

        response = self.client.put(
            f"/issues/{self.issue_id}",
            json={"status": "under_review"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "under_review"
        updates_arg = mock_update_by_id.call_args[0][3]
        assert "resolution_note" not in updates_arg
        mock_log_entity_change.assert_called_once()

    def test_update_issue_invalid_status_returns_422(self):
        response = self.client.put(
            f"/issues/{self.issue_id}",
            json={"status": "invalid_status"},
        )
        assert response.status_code == 422
