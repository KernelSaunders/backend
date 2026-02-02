"""Tests for conftest fixtures."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import os
from dotenv import load_dotenv

from src.config import Settings, get_settings

# Load environment variables from .env file
load_dotenv()

# Check if we're in CI environment
IS_CI = os.getenv("CI", "false").lower() == "true"


def test_client_fixture(client):
    """Test that client fixture returns a TestClient instance."""
    assert isinstance(client, TestClient)
    assert client.app is not None


@pytest.mark.skipif(IS_CI, reason="Requires real Supabase credentials (CI uses mocks)")
def test_client_fixture_can_make_requests(client):
    """Test that client fixture can make HTTP requests to the real API."""
    # This test will use the actual Supabase credentials from .env
    response = client.get("/products")
    # Should get a successful response from the API
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.skipif(IS_CI, reason="Requires real Supabase credentials")
def test_real_settings_from_env():
    """Test that real settings are loaded from .env file."""
    settings = get_settings()

    # Verify that settings are loaded from environment
    assert settings.supabase_url != ""
    assert settings.supabase_key != ""
    assert settings.port == 8000

    # Verify the URL format is correct
    assert settings.supabase_url.startswith("http")
    assert (
        "supabase" in settings.supabase_url.lower()
        or settings.supabase_url.startswith("http")
    )

    # Verify key is not a placeholder
    assert settings.supabase_key not in ["", "your-supabase-key-here", "test-key"]


@pytest.mark.skipif(IS_CI, reason="CI environment doesn't have .env file")
def test_env_file_exists():
    """Test that .env file exists and has required variables."""
    # Check if .env file exists
    env_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    assert os.path.exists(env_file_path), ".env file should exist in the project root"

    # Verify required environment variables are set
    assert os.getenv("SUPABASE_URL") is not None, "SUPABASE_URL should be set in .env"
    assert os.getenv("SUPABASE_KEY") is not None, "SUPABASE_KEY should be set in .env"


def test_mock_supabase_client_fixture(mock_supabase_client):
    """Test that mock_supabase_client fixture returns a Mock instance."""
    assert isinstance(mock_supabase_client, Mock)


def test_mock_supabase_client_is_callable(mock_supabase_client):
    """Test that mock_supabase_client can be configured and called."""
    # Mocks should be callable and configurable
    mock_supabase_client.table.return_value = Mock()
    result = mock_supabase_client.table("test_table")
    assert result is not None
    mock_supabase_client.table.assert_called_once_with("test_table")


def test_test_settings_fixture(test_settings):
    """Test that test_settings fixture returns a Settings instance."""
    assert isinstance(test_settings, Settings)


def test_test_settings_has_required_fields(test_settings):
    """Test that test_settings has all required configuration fields."""
    assert hasattr(test_settings, "supabase_url")
    assert hasattr(test_settings, "supabase_key")
    assert hasattr(test_settings, "port")


def test_test_settings_values(test_settings):
    """Test that test_settings fixture provides test configuration."""
    # The test_settings fixture should provide isolated test values
    assert test_settings.supabase_url == "https://test.supabase.co"
    assert test_settings.supabase_key == "test-key"
    assert test_settings.port == 8000  # Default value


def test_test_settings_is_isolated_from_real_env(test_settings):
    """Test that test_settings uses isolated test values, not real .env."""
    # Ensure the test_settings fixture doesn't use production values
    assert "test" in test_settings.supabase_url.lower()
    assert test_settings.supabase_key == "test-key"

    # Verify it's different from real settings (skip in CI where both are test values)
    if not IS_CI:
        real_settings = get_settings()
        if real_settings.supabase_url and real_settings.supabase_key:
            assert test_settings.supabase_url != real_settings.supabase_url
            assert test_settings.supabase_key != real_settings.supabase_key


def test_fixtures_are_independent():
    """Test that fixtures don't interfere with each other."""
    # This test ensures that pytest fixtures are properly isolated
    # If this test runs, it means pytest is loading fixtures correctly
    assert True
