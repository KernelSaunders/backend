"""Tests for src/main.py application wiring (lifespan, CORS, FastAPI factory)."""

from unittest.mock import patch

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

import src.main as main_module
from src.main import app, lifespan, settings


def _cors_middleware_options():
    """Return kwargs dict for the first CORSMiddleware on the app, or None."""
    for mw in app.user_middleware:
        if mw.cls is CORSMiddleware:
            return dict(mw.kwargs)
    return None


class TestLifespan:
    def test_lifespan_calls_get_client_during_startup(self):
        with patch("src.main.get_client") as mock_get_client:
            with TestClient(app):
                pass
        mock_get_client.assert_called_once()

    def test_lifespan_yields_without_shutdown_side_effects(self):
        """Startup runs; no teardown logic after yield in current implementation."""
        with patch("src.main.get_client"):
            with TestClient(app) as client:
                assert client.app is app


class TestCORSMiddleware:
    def test_cors_middleware_is_registered(self):
        assert _cors_middleware_options() is not None

    def test_cors_allow_origins_matches_settings_frontend_url(self):
        opts = _cors_middleware_options()
        assert opts["allow_origins"] == [settings.frontend_url]

    def test_cors_allow_credentials_true(self):
        assert _cors_middleware_options()["allow_credentials"] is True

    def test_cors_allow_methods_wildcard(self):
        assert _cors_middleware_options()["allow_methods"] == ["*"]

    def test_cors_allow_headers_wildcard(self):
        assert _cors_middleware_options()["allow_headers"] == ["*"]


class TestFastAPIFactory:
    def test_app_is_fastapi_instance(self):
        assert isinstance(app, FastAPI)

    def test_lifespan_bound_to_same_callable(self):
        """The router should use the module-level asynccontextmanager lifespan."""
        assert app.router.lifespan_context is lifespan

    def test_routers_mounted(self):
        route_paths = []
        for r in app.routes:
            p = getattr(r, "path", None)
            if p:
                route_paths.append(p)
        assert any(p.startswith("/products") for p in route_paths)
        assert any(p.startswith("/missions") for p in route_paths)
        assert any(p.startswith("/users") for p in route_paths)
        assert any(p.startswith("/issues") for p in route_paths)
