"""Shared test fixtures and configuration for pytest."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock

from src.main import app
from src.config import Settings


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
