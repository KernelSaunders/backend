from fastapi import APIRouter, Depends

from ..auth import get_current_user_id, get_current_user_role
from ..database import select_all, select_by_field
from ..models.user import QuestMission, UserProgress, UserRole

router = APIRouter(prefix="/users", tags=["users"])


def build_badges(
    total_completed: int,
    missions_completed_by_tier: dict[str, int],
    mission_counts_by_tier: dict[str, int],
) -> list[dict]:
    total_missions = sum(mission_counts_by_tier.values())

    return [
        {
            "id": "first_steps",
            "name": "First Steps",
            "description": "Complete your first mission",
            "earned": total_completed >= 1,
            "progress_current": min(total_completed, 1),
            "progress_target": 1,
            "icon": "1",
        },
        {
            "id": "getting_going",
            "name": "Getting Going",
            "description": "Complete 3 missions",
            "earned": total_completed >= 3,
            "progress_current": min(total_completed, 3),
            "progress_target": 3,
            "icon": "3",
        },
        {
            "id": "explorer",
            "name": "Explorer",
            "description": "Complete 6 missions",
            "earned": total_completed >= 6,
            "progress_current": min(total_completed, 6),
            "progress_target": 6,
            "icon": "6",
        },
        {
            "id": "basic_complete",
            "name": "Basic Complete",
            "description": "Complete every basic mission",
            "earned": mission_counts_by_tier["basic"] > 0
            and missions_completed_by_tier["basic"] >= mission_counts_by_tier["basic"],
            "progress_current": missions_completed_by_tier["basic"],
            "progress_target": mission_counts_by_tier["basic"],
            "icon": "B",
        },
        {
            "id": "intermediate_complete",
            "name": "Intermediate Complete",
            "description": "Complete every intermediate mission",
            "earned": mission_counts_by_tier["intermediate"] > 0
            and missions_completed_by_tier["intermediate"]
            >= mission_counts_by_tier["intermediate"],
            "progress_current": missions_completed_by_tier["intermediate"],
            "progress_target": mission_counts_by_tier["intermediate"],
            "icon": "I",
        },
        {
            "id": "advanced_complete",
            "name": "Advanced Complete",
            "description": "Complete every advanced mission",
            "earned": mission_counts_by_tier["advanced"] > 0
            and missions_completed_by_tier["advanced"]
            >= mission_counts_by_tier["advanced"],
            "progress_current": missions_completed_by_tier["advanced"],
            "progress_target": mission_counts_by_tier["advanced"],
            "icon": "A",
        },
        {
            "id": "quest_master",
            "name": "Quest Master",
            "description": "Complete every mission",
            "earned": total_missions > 0 and total_completed >= total_missions,
            "progress_current": total_completed,
            "progress_target": total_missions,
            "icon": "*",
        },
    ]


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
    mission_counts_by_tier = {
        "basic": 0,
        "intermediate": 0,
        "advanced": 0,
    }
    by_tier = {
        "basic": 0,
        "intermediate": 0,
        "advanced": 0,
    }
    mission_progress = []
    recent_completions = []

    for mission in missions:
        mission_counts_by_tier[mission.tier] += 1

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
    badges = build_badges(total_completed, by_tier, mission_counts_by_tier)

    return {
        "user_id": user_id,
        "total_completed": total_completed,
        "total_points": total_points,
        "missions_completed_by_tier": by_tier,
        "missions": mission_progress,
        "recent_completions": recent_completions,
        "badges": badges,
    }
