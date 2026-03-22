"""Tests for run.py CLI entrypoint."""

from unittest.mock import MagicMock, patch

import run


class TestRunMain:
    def test_main_calls_uvicorn_run_with_expected_arguments(self):
        mock_settings = MagicMock()
        mock_settings.port = 9123

        with patch("run.get_settings", return_value=mock_settings):
            with patch("run.uvicorn.run") as mock_uvicorn_run:
                run.main()

        mock_uvicorn_run.assert_called_once_with(
            "src.main:app",
            host="0.0.0.0",
            port=9123,
            reload=True,
        )

    def test_main_uses_port_from_settings(self):
        mock_settings = MagicMock()
        mock_settings.port = 8000

        with patch("run.get_settings", return_value=mock_settings):
            with patch("run.uvicorn.run") as mock_uvicorn_run:
                run.main()

        assert mock_uvicorn_run.call_args.kwargs["port"] == 8000
