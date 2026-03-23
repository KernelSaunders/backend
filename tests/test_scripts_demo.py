"""Tests for scripts/demo.py demo script."""

import importlib.util
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_DEMO_PATH = _PROJECT_ROOT / "scripts" / "demo.py"


def _load_demo_module():
    spec = importlib.util.spec_from_file_location("scripts_demo", _DEMO_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def demo_module():
    return _load_demo_module()


class TestDemoMain:
    def test_main_calls_select_all_for_each_model(self, demo_module, capsys):
        from src.models import Product, Stage, InputShare

        p = Product(
            product_id="p1",
            name="N",
            category="food",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 1),
        )
        s = Stage(stage_id="s1", stage_type="grow", location_country="US")
        sh = InputShare(
            input_id="i1",
            input_name="wheat",
            country="CA",
            percentage=Decimal("10"),
            created_at=datetime(2024, 1, 1),
        )

        with patch.object(demo_module, "select_all", side_effect=[[p], [s], [sh]]) as mock_sa:
            demo_module.main()

        assert mock_sa.call_count == 3
        mock_sa.assert_any_call(Product)
        mock_sa.assert_any_call(Stage)
        mock_sa.assert_any_call(InputShare)

        out = capsys.readouterr().out
        assert "Products:" in out
        assert "N" in out
        assert "Stages:" in out
        assert "grow" in out
        assert "Input Shares:" in out
        assert "wheat" in out
        assert "10" in out

    def test_main_handles_empty_lists(self, demo_module, capsys):
        with patch.object(demo_module, "select_all", return_value=[]):
            demo_module.main()
        out = capsys.readouterr().out
        assert "Products:" in out
        assert "Stages:" in out
        assert "Input Shares:" in out
