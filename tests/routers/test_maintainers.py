"""Tests for maintainers router: fetch_row, resolve_product_details, get_audit_logs."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.auth import get_current_user_id, require_maintainer
from src.main import app
from src.models.user import UserRole
from src.routers.maintainers import fetch_row, resolve_product_details

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PRODUCT_ID = "aaaaaaaa-0000-0000-0000-000000000001"
STAGE_ID = "bbbbbbbb-0000-0000-0000-000000000002"
CLAIM_ID = "cccccccc-0000-0000-0000-000000000003"
ISSUE_ID = "dddddddd-0000-0000-0000-000000000004"
INPUT_ID = "eeeeeeee-0000-0000-0000-000000000005"
EVIDENCE_ID = "ffffffff-0000-0000-0000-000000000006"
USER_ID = "00000000-0000-0000-0000-000000000001"

MAINTAINER_ROLE = UserRole(
    role_id="role-0001",
    user_id=USER_ID,
    role="maintainer",
    created_at=datetime(2026, 1, 1),
)


def _make_client():
    """Return a TestClient with maintainer auth overrides active."""
    from fastapi.testclient import TestClient

    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    app.dependency_overrides[require_maintainer] = lambda: MAINTAINER_ROLE
    return TestClient(app)


# ---------------------------------------------------------------------------
# fetch_row
# ---------------------------------------------------------------------------


class TestFetchRow:
    @patch("src.routers.maintainers.get_client")
    def test_returns_row_dict_when_found(self, mock_get_client):
        mock_response = MagicMock()
        mock_response.data = [{"product_id": PRODUCT_ID, "name": "Widget"}]
        mock_get_client.return_value.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = (
            mock_response
        )

        result = fetch_row("Product", "product_id", PRODUCT_ID)

        assert result == {"product_id": PRODUCT_ID, "name": "Widget"}

    @patch("src.routers.maintainers.get_client")
    def test_returns_none_when_no_data(self, mock_get_client):
        mock_response = MagicMock()
        mock_response.data = []
        mock_get_client.return_value.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = (
            mock_response
        )

        result = fetch_row("Product", "product_id", PRODUCT_ID)

        assert result is None

    @patch("src.routers.maintainers.get_client")
    def test_returns_none_when_row_is_not_dict(self, mock_get_client):
        mock_response = MagicMock()
        mock_response.data = ["not-a-dict"]
        mock_get_client.return_value.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = (
            mock_response
        )

        result = fetch_row("Product", "product_id", PRODUCT_ID)

        assert result is None


# ---------------------------------------------------------------------------
# resolve_product_details
# ---------------------------------------------------------------------------


def _mock_fetch(return_map: dict):
    """
    Return a side_effect function for fetch_row that maps
    (table_name, id_field, id_value) → return_map.get(table_name).
    """

    def _side(table_name, id_field, id_value):
        return return_map.get(table_name)

    return _side


class TestResolveProductDetails:
    def test_returns_none_when_entity_id_not_string(self):
        entry = {"entity_type": "product", "entity_id": 123}
        assert resolve_product_details(entry) is None

    @patch("src.routers.maintainers.fetch_row")
    def test_product_entity_type(self, mock_fetch):
        mock_fetch.side_effect = _mock_fetch(
            {"Product": {"product_id": PRODUCT_ID, "name": "Widget"}}
        )
        entry = {"entity_type": "product", "entity_id": PRODUCT_ID, "change_summary": {}}
        result = resolve_product_details(entry)
        assert result == {
            "product_id": PRODUCT_ID,
            "product_name": "Widget",
            "product_link": f"/dashboard/products/{PRODUCT_ID}/edit",
        }

    @patch("src.routers.maintainers.fetch_row")
    def test_stage_entity_type(self, mock_fetch):
        mock_fetch.side_effect = _mock_fetch(
            {
                "Stage": {"stage_id": STAGE_ID, "product_id": PRODUCT_ID},
                "Product": {"product_id": PRODUCT_ID, "name": "Widget"},
            }
        )
        entry = {"entity_type": "stage", "entity_id": STAGE_ID, "change_summary": {}}
        result = resolve_product_details(entry)
        assert result["product_id"] == PRODUCT_ID

    @patch("src.routers.maintainers.fetch_row")
    def test_claim_entity_type(self, mock_fetch):
        mock_fetch.side_effect = _mock_fetch(
            {
                "Claim": {"claim_id": CLAIM_ID, "product_id": PRODUCT_ID},
                "Product": {"product_id": PRODUCT_ID, "name": "Widget"},
            }
        )
        entry = {"entity_type": "claim", "entity_id": CLAIM_ID, "change_summary": {}}
        result = resolve_product_details(entry)
        assert result["product_id"] == PRODUCT_ID

    @patch("src.routers.maintainers.fetch_row")
    def test_issue_entity_type(self, mock_fetch):
        mock_fetch.side_effect = _mock_fetch(
            {
                "IssueReports": {"issue_id": ISSUE_ID, "product_id": PRODUCT_ID},
                "Product": {"product_id": PRODUCT_ID, "name": "Widget"},
            }
        )
        entry = {"entity_type": "issue", "entity_id": ISSUE_ID, "change_summary": {}}
        result = resolve_product_details(entry)
        assert result["product_id"] == PRODUCT_ID

    @patch("src.routers.maintainers.fetch_row")
    def test_input_share_entity_type(self, mock_fetch):
        mock_fetch.side_effect = _mock_fetch(
            {
                "InputShare": {"input_id": INPUT_ID, "product_id": PRODUCT_ID},
                "Product": {"product_id": PRODUCT_ID, "name": "Widget"},
            }
        )
        entry = {
            "entity_type": "input_share",
            "entity_id": INPUT_ID,
            "change_summary": {},
        }
        result = resolve_product_details(entry)
        assert result["product_id"] == PRODUCT_ID

    @patch("src.routers.maintainers.fetch_row")
    def test_evidence_with_claim_id_in_summary(self, mock_fetch):
        mock_fetch.side_effect = _mock_fetch(
            {
                "Claim": {"claim_id": CLAIM_ID, "product_id": PRODUCT_ID},
                "Product": {"product_id": PRODUCT_ID, "name": "Widget"},
            }
        )
        entry = {
            "entity_type": "evidence",
            "entity_id": EVIDENCE_ID,
            "change_summary": {"claim_id": CLAIM_ID},
        }
        result = resolve_product_details(entry)
        assert result["product_id"] == PRODUCT_ID

    @patch("src.routers.maintainers.fetch_row")
    def test_evidence_without_summary_resolves_via_evidence_claim_id(self, mock_fetch):
        mock_fetch.side_effect = _mock_fetch(
            {
                "Evidence": {"evidence_id": EVIDENCE_ID, "claim_id": CLAIM_ID, "stage_id": None},
                "Claim": {"claim_id": CLAIM_ID, "product_id": PRODUCT_ID},
                "Product": {"product_id": PRODUCT_ID, "name": "Widget"},
            }
        )
        entry = {
            "entity_type": "evidence",
            "entity_id": EVIDENCE_ID,
            "change_summary": {},
        }
        result = resolve_product_details(entry)
        assert result["product_id"] == PRODUCT_ID

    @patch("src.routers.maintainers.fetch_row")
    def test_evidence_without_claim_id_resolves_via_stage(self, mock_fetch):
        mock_fetch.side_effect = _mock_fetch(
            {
                "Evidence": {"evidence_id": EVIDENCE_ID, "claim_id": None, "stage_id": STAGE_ID},
                "Stage": {"stage_id": STAGE_ID, "product_id": PRODUCT_ID},
                "Product": {"product_id": PRODUCT_ID, "name": "Widget"},
            }
        )
        entry = {
            "entity_type": "evidence",
            "entity_id": EVIDENCE_ID,
            "change_summary": {},
        }
        result = resolve_product_details(entry)
        assert result["product_id"] == PRODUCT_ID

    @patch("src.routers.maintainers.fetch_row")
    def test_returns_none_when_product_not_found(self, mock_fetch):
        mock_fetch.side_effect = _mock_fetch(
            {"Product": None}
        )
        entry = {"entity_type": "product", "entity_id": PRODUCT_ID, "change_summary": {}}
        result = resolve_product_details(entry)
        assert result is None

    @patch("src.routers.maintainers.fetch_row")
    def test_returns_none_for_unknown_entity_type(self, mock_fetch):
        entry = {"entity_type": "unknown_thing", "entity_id": PRODUCT_ID, "change_summary": {}}
        result = resolve_product_details(entry)
        assert result is None

    @patch("src.routers.maintainers.fetch_row")
    def test_product_name_falls_back_to_id_when_name_empty(self, mock_fetch):
        mock_fetch.side_effect = _mock_fetch(
            {"Product": {"product_id": PRODUCT_ID, "name": ""}}
        )
        entry = {"entity_type": "product", "entity_id": PRODUCT_ID, "change_summary": {}}
        result = resolve_product_details(entry)
        assert result["product_name"] == PRODUCT_ID

    @patch("src.routers.maintainers.fetch_row")
    def test_returns_none_when_stage_has_no_product_id(self, mock_fetch):
        mock_fetch.side_effect = _mock_fetch(
            {"Stage": None}
        )
        entry = {"entity_type": "stage", "entity_id": STAGE_ID, "change_summary": {}}
        result = resolve_product_details(entry)
        assert result is None


# ---------------------------------------------------------------------------
# GET /maintainers/audit-logs
# ---------------------------------------------------------------------------


class TestGetAuditLogs:
    def setup_method(self):
        self.client = _make_client()

    def teardown_method(self):
        app.dependency_overrides.clear()

    @patch("src.routers.maintainers.get_client")
    def test_returns_empty_list_when_no_logs(self, mock_get_client):
        mock_response = MagicMock()
        mock_response.data = []
        (
            mock_get_client.return_value.table.return_value.select.return_value
            .order.return_value.limit.return_value.execute.return_value
        ) = mock_response

        response = self.client.get("/maintainers/audit-logs")

        assert response.status_code == 200
        assert response.json() == []

    @patch("src.routers.maintainers.resolve_product_details")
    @patch("src.routers.maintainers.get_client")
    def test_returns_enriched_log_entries(self, mock_get_client, mock_resolve):
        log_entry = {
            "log_id": "log-001",
            "entity_type": "product",
            "entity_id": PRODUCT_ID,
            "changed_by": USER_ID,
            "change_summary": {"action": "created"},
            "timestamp": "2026-01-01T00:00:00",
        }
        mock_response = MagicMock()
        mock_response.data = [log_entry]
        (
            mock_get_client.return_value.table.return_value.select.return_value
            .order.return_value.limit.return_value.execute.return_value
        ) = mock_response
        mock_resolve.return_value = {
            "product_id": PRODUCT_ID,
            "product_name": "Widget",
            "product_link": f"/dashboard/products/{PRODUCT_ID}/edit",
        }

        response = self.client.get("/maintainers/audit-logs")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["product"]["product_id"] == PRODUCT_ID
        assert data[0]["log_id"] == "log-001"

    @patch("src.routers.maintainers.resolve_product_details")
    @patch("src.routers.maintainers.get_client")
    def test_skips_non_dict_entries(self, mock_get_client, mock_resolve):
        mock_response = MagicMock()
        mock_response.data = ["not-a-dict", None]
        (
            mock_get_client.return_value.table.return_value.select.return_value
            .order.return_value.limit.return_value.execute.return_value
        ) = mock_response

        response = self.client.get("/maintainers/audit-logs")

        assert response.status_code == 200
        assert response.json() == []
        mock_resolve.assert_not_called()

    @patch("src.routers.maintainers.get_client")
    def test_respects_limit_query_param(self, mock_get_client):
        mock_response = MagicMock()
        mock_response.data = []
        chain = (
            mock_get_client.return_value.table.return_value.select.return_value
            .order.return_value
        )
        chain.limit.return_value.execute.return_value = mock_response

        self.client.get("/maintainers/audit-logs?limit=10")

        chain.limit.assert_called_once_with(10)

    def test_requires_maintainer_role(self):
        app.dependency_overrides.clear()
        from fastapi.testclient import TestClient

        plain_client = TestClient(app)
        response = plain_client.get("/maintainers/audit-logs")
        assert response.status_code in (401, 422)

    @patch("src.routers.maintainers.get_client")
    def test_product_null_when_resolve_returns_none(self, mock_get_client):
        log_entry = {
            "log_id": "log-002",
            "entity_type": "unknown",
            "entity_id": "xyz",
            "changed_by": USER_ID,
            "change_summary": {},
            "timestamp": "2026-01-01T00:00:00",
        }
        mock_response = MagicMock()
        mock_response.data = [log_entry]
        (
            mock_get_client.return_value.table.return_value.select.return_value
            .order.return_value.limit.return_value.execute.return_value
        ) = mock_response

        response = self.client.get("/maintainers/audit-logs")

        assert response.status_code == 200
        assert response.json()[0]["product"] is None
