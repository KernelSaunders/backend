"""Shared test fixtures and configuration for pytest."""

from datetime import datetime
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from src.auth import get_current_user_id, require_verifier
from src.config import Settings
from src.main import app
from src.models.user import UserRole


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing without database calls."""
    return Mock()


@pytest.fixture
def test_settings():
    """Provide test settings."""
    return Settings(supabase_url="https://test.supabase.co", supabase_key="test-key")


# Mock client for authentication
TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_VERIFIER_ROLE = UserRole(
    role_id="role-00000000-0000-0000-0000-000000000001",
    user_id=TEST_USER_ID,
    role="verifier",
    created_at=datetime(2026, 1, 1),
)


@pytest.fixture
def verifier_client():
    """Test client with verifier auth overrides."""
    app.dependency_overrides[get_current_user_id] = lambda: TEST_USER_ID
    app.dependency_overrides[require_verifier] = lambda: TEST_VERIFIER_ROLE
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
