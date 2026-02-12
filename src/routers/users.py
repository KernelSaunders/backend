from fastapi import APIRouter, Depends

from ..auth import get_current_user_id, get_current_user_role
from ..models.user import UserRole

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me/role")
async def get_my_role(
    user_id: str = Depends(get_current_user_id),
    role: UserRole | None = Depends(get_current_user_role)
):
    user_role = None
    if role is not None:
        user_role = role.role
    
    return {
        "user_id": user_id,
        "role": user_role
    }