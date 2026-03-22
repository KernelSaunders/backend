"""Unit tests for Pydantic schemas in src.routers.missions."""

import pytest
from pydantic import ValidationError

from src.routers.missions import MissionAttemptIn, MissionAttemptOut


class TestMissionAttemptIn:
    def test_valid_non_negative_index(self):
        assert MissionAttemptIn(option_index=0).option_index == 0
        assert MissionAttemptIn(option_index=3).option_index == 3

    def test_negative_index_allowed_by_schema(self):
        """API layer returns 422 for negative index; model itself allows int."""
        body = MissionAttemptIn(option_index=-1)
        assert body.option_index == -1

    def test_missing_option_index_rejected(self):
        with pytest.raises(ValidationError) as exc:
            MissionAttemptIn()  # type: ignore[call-arg]
        assert any(e["loc"] == ("option_index",) for e in exc.value.errors())

    def test_option_index_rejects_non_coercible_value(self):
        with pytest.raises(ValidationError) as exc:
            MissionAttemptIn(option_index="not-a-number")  # type: ignore[arg-type]
        assert any(e["loc"] == ("option_index",) for e in exc.value.errors())

    def test_numeric_string_coerced_to_int(self):
        """Pydantic may coerce strict-looking strings to int."""
        body = MissionAttemptIn(option_index="2")  # type: ignore[arg-type]
        assert body.option_index == 2

    def test_model_dump(self):
        assert MissionAttemptIn(option_index=2).model_dump() == {"option_index": 2}


class TestMissionAttemptOut:
    def test_correct_true(self):
        assert MissionAttemptOut(correct=True).correct is True

    def test_correct_false(self):
        assert MissionAttemptOut(correct=False).correct is False

    def test_missing_correct_rejected(self):
        with pytest.raises(ValidationError) as exc:
            MissionAttemptOut()  # type: ignore[call-arg]
        assert any(e["loc"] == ("correct",) for e in exc.value.errors())

    def test_correct_rejects_wrong_type(self):
        with pytest.raises(ValidationError) as exc:
            MissionAttemptOut(correct=[])  # type: ignore[arg-type]
        assert any(e["loc"] == ("correct",) for e in exc.value.errors())

    def test_model_dump(self):
        assert MissionAttemptOut(correct=True).model_dump() == {"correct": True}
