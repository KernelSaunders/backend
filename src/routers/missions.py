from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..database import select_by_id
from ..models import QuestMission


def validate_uuid(value: str, field_name: str = "id") -> str:
    """Validate that a string is a valid UUID format."""
    try:
        UUID(value)
        return value
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name} format")


router = APIRouter(prefix="/missions", tags=["missions"])


# request body
class MissionAttemptIn(BaseModel):
    option_index: int


# return body
class MissionAttemptOut(BaseModel):
    correct: bool


def _norm_answer(value: str) -> str:
    # Some questions have mnual user string input
    # so we should sanitise it before checking answer
    return value.strip().casefold()


@router.post("/{mission_id}/attempts", response_model=MissionAttemptOut)
def create_attempt(mission_id: str, attempt: MissionAttemptIn) -> MissionAttemptOut:
    """
        Validate an attempt and return correctness.
    .
    """
    validate_uuid(mission_id, "mission_id")
    mission = select_by_id(QuestMission, "mission_id", mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    answer_key = mission.answer_key or {}
    options = answer_key.get("options")
    correct = answer_key.get("correct")

    # validate the mission first (options are correct, answer is an option)
    if not isinstance(options, list) or not all(isinstance(o, str) for o in options):
        raise HTTPException(
            status_code=500, detail="Mission is not attemptable (invalid options)"
        )
    if not isinstance(correct, str):
        raise HTTPException(
            status_code=500,
            detail="Mission is not attemptable (invalid correct answer)",
        )

    if attempt.option_index < 0 or attempt.option_index >= len(options):
        raise HTTPException(status_code=422, detail="option_index out of range")

    chosen = options[attempt.option_index]
    return MissionAttemptOut(correct=_norm_answer(chosen) == _norm_answer(correct))
