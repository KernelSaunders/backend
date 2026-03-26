from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import get_current_user_id
from ..database import get_client, select_by_field, select_by_id
from ..models import QuestMission, UserProgress


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
    model_config = {"populate_by_name": True}

    correct: bool
    points_awarded: int | None = None
    completed: bool | None = None
    attempts: int | None = None

    def model_dump(self, **kwargs):
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)


def mission_points(tier: str) -> int:
    """Basic=10, Intermediate=20, Advanced=30"""
    if tier == "basic":
        return 10
    elif tier == "intermediate":
        return 20
    elif tier == "advanced":
        return 30
    return 0


def upsert_user_progress(
    user_id: str, mission: QuestMission, correct: bool
) -> tuple[UserProgress, int]:
    client = get_client()
    user_progress = select_by_field(UserProgress, "user_id", user_id)

    # UserProgress keeps one row per user/mission pair, so we reuse the
    # existing record to work out completion state and attempt count.
    existing = None
    for progress in user_progress:
        if progress.mission_id == mission.mission_id:
            existing = progress
            break

    already_completed = False
    if existing is not None:
        already_completed = existing.completed

    attempts = 0
    if existing is not None:
        if isinstance(existing.attempts, int):
            attempts = existing.attempts

    attempts += 1

    updates = {
        "user_id": user_id,
        "mission_id": mission.mission_id,
        "attempts": attempts,
    }

    if correct:
        # We only add completion time the first time a mission is cleared
        updates["completed"] = True
        updates["score"] = mission_points(mission.tier)
        if not existing or existing.completed_at is None:
            updates["completed_at"] = datetime.now(timezone.utc).isoformat()
    else:
        updates["completed"] = False
        updates["score"] = 0

    if existing:
        result = (
            client.table("UserProgress")
            .update(updates)
            .eq("user_id", user_id)
            .eq("mission_id", mission.mission_id)
            .execute()
        )
    else:
        result = client.table("UserProgress").insert(updates).execute()

    # Points are only earned on the first successful completion.
    points_awarded = (
        mission_points(mission.tier) if correct and not already_completed else 0
    )
    return UserProgress.model_validate(result.data[0]), points_awarded


def _norm_answer(value: str) -> str:
    # Some questions have mnual user string input
    # so we should sanitise it before checking answer
    return value.strip().casefold()


@router.post("/{mission_id}/attempts", response_model=MissionAttemptOut, response_model_exclude_none=True)
def create_attempt(
    mission_id: str,
    attempt: MissionAttemptIn,
    user_id: str = Depends(get_current_user_id),
) -> MissionAttemptOut:
    """
    Validate an attempt and return correctness.
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
    is_correct = _norm_answer(chosen) == _norm_answer(correct)

    progress, points_awarded = upsert_user_progress(user_id, mission, is_correct)
    completed = progress.completed
    attempts = progress.attempts

    return MissionAttemptOut(
        correct=is_correct,
        points_awarded=points_awarded,
        completed=completed,
        attempts=attempts,
    )
