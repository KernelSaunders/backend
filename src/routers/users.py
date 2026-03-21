from fastapi import APIRouter, Depends

from ..auth import get_current_user_id, get_current_user_role
from ..database import select_all, select_by_field
from ..models.user import QuestMission, UserProgress, UserRole

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/role")
async def get_my_role(
    user_id: str = Depends(get_current_user_id),
    role: UserRole | None = Depends(get_current_user_role),
):
    user_role = "consumer"  # default if not verifier (will change)
    if role is not None:
        user_role = role.role

    return {"user_id": user_id, "role": user_role}


@router.get("/me/progress")
async def get_my_progress(user_id: str = Depends(get_current_user_id)):
    """
    Return signed in user progress; missions by tier, points
    """
    progress_rows = select_by_field(UserProgress, "user_id", user_id)
    missions = select_all(QuestMission)
    mission_lookup = {mission.mission_id: mission for mission in missions}

    total_points = 0
    total_completed = 0
    by_tier = {
        "basic": 0,
        "intermediate": 0,
        "advanced": 0,
    }
    mission_progress = []
    recent_completions = []

    # Build a lightweight summary the frontend can use for totals and history
    for progress in progress_rows:
        mission = mission_lookup.get(progress.mission_id)
        if mission is None:
            continue

        completed = progress.completed
        score = progress.score or 0
        completed_at = progress.completed_at

        if completed:
            total_completed += 1
            total_points += score
            by_tier[mission.tier] += 1
            if completed_at is not None:
                recent_completions.append(
                    {
                        "mission_id": mission.mission_id,
                        "question": mission.question,
                        "tier": mission.tier,
                        "score": score,
                        "completed_at": completed_at,
                    }
                )

        mission_progress.append(
            {
                "mission_id": mission.mission_id,
                "tier": mission.tier,
                "completed": completed,
                "score": score,
                "attempts": progress.attempts,
                "completed_at": completed_at,
            }
        )

    recent_completions.sort(key=lambda item: item["completed_at"], reverse=True)

    return {
        "user_id": user_id,
        "total_completed": total_completed,
        "total_points": total_points,
        "missions_completed_by_tier": by_tier,
        "missions": mission_progress,
        "recent_completions": recent_completions,
    }
