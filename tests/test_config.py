"""Tests for config module."""

import pytest
from pydantic import ValidationError
from unittest.mock import patch

from src.config import Settings, get_settings


def _clear_settings_env(monkeypatch):
    """Remove config-related env vars so BaseSettings uses field defaults."""
    for key in (
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "FRONTEND_URL",
        "PORT",
    ):
        monkeypatch.delenv(key, raising=False)


class TestSettings:
    """Test suite for Settings configuration class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        get_settings.cache_clear()

    def teardown_method(self):
        """Clean up after each test method."""
        get_settings.cache_clear()

    def test_settings_initialization_with_defaults(self, monkeypatch):
        """Test Settings initialization with default values."""
        _clear_settings_env(monkeypatch)
        settings = Settings(_env_file=None)
        assert settings.supabase_url == ""
        assert settings.supabase_key == ""
        assert settings.frontend_url == "http://localhost:3000"
        assert settings.port == 8000

    def test_settings_initialization_with_env_vars(self, monkeypatch):
        """Test Settings initialization with environment variables."""
        _clear_settings_env(monkeypatch)
        monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "secret-service-key")
        monkeypatch.setenv("FRONTEND_URL", "https://app.example.com")
        monkeypatch.setenv("PORT", "9000")

        settings = Settings(_env_file=None)
        assert settings.supabase_url == "https://example.supabase.co"
        assert settings.supabase_key == "secret-service-key"
        assert settings.frontend_url == "https://app.example.com"
        assert settings.port == 9000

    def test_settings_supabase_url_validation(self, monkeypatch):
        """Supabase URL accepts string values (no extra schema beyond str)."""
        _clear_settings_env(monkeypatch)
        monkeypatch.setenv("SUPABASE_URL", "https://project-ref.supabase.co")
        assert Settings(_env_file=None).supabase_url == "https://project-ref.supabase.co"

    def test_settings_supabase_key_validation(self, monkeypatch):
        """Supabase key accepts string values."""
        _clear_settings_env(monkeypatch)
        monkeypatch.setenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.fake")
        assert (
            Settings(_env_file=None).supabase_key
            == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.fake"
        )

    def test_settings_port_default_value(self, monkeypatch):
        """Test default port value is 8000."""
        _clear_settings_env(monkeypatch)
        assert Settings(_env_file=None).port == 8000

    def test_settings_port_custom_value(self, monkeypatch):
        """Test custom port value from environment."""
        _clear_settings_env(monkeypatch)
        monkeypatch.setenv("PORT", "3000")
        assert Settings(_env_file=None).port == 3000

    def test_settings_port_invalid_env_raises(self, monkeypatch):
        """Non-integer PORT env value fails validation."""
        _clear_settings_env(monkeypatch)
        monkeypatch.setenv("PORT", "not-a-port")
        with pytest.raises(ValidationError) as exc_info:
            Settings(_env_file=None)
        assert any(err["loc"] == ("port",) for err in exc_info.value.errors())


class TestGetSettings:
    """Test suite for get_settings function."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        get_settings.cache_clear()

    def teardown_method(self):
        """Clean up after each test method."""
        get_settings.cache_clear()

    def test_get_settings_returns_settings_instance(self, monkeypatch):
        """Test that get_settings returns a Settings instance."""
        _clear_settings_env(monkeypatch)
        get_settings.cache_clear()
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_caching(self, monkeypatch):
        """Test that get_settings uses lru_cache correctly."""
        _clear_settings_env(monkeypatch)
        get_settings.cache_clear()
        with patch("src.config.Settings") as mock_settings_cls:
            mock_instance = mock_settings_cls.return_value
            mock_settings_cls.reset_mock()

            get_settings()
            get_settings()

            mock_settings_cls.assert_called_once()
            assert get_settings() is mock_instance

    def test_get_settings_returns_same_instance(self, monkeypatch):
        """Test that multiple calls return the same cached instance."""
        _clear_settings_env(monkeypatch)
        get_settings.cache_clear()
        first = get_settings()
        second = get_settings()
        assert first is second
