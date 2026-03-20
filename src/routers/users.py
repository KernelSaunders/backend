from fastapi import APIRouter, Depends

from ..auth import get_current_user_id, get_current_user_role, resolve_role_name
from ..models.user import UserRole

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me/role")
async def get_my_role(
    user_id: str = Depends(get_current_user_id),
    role: UserRole | None = Depends(get_current_user_role),
):
    return {
        "user_id": user_id,
        "role": resolve_role_name(role)
    }
