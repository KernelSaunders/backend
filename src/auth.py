from typing import Literal

from fastapi import Depends, HTTPException, Header
from supabase import Client

from .database import get_client, select_by_field
from .models.user import UserRole

# default as consumer (if not logged in)
RoleName = Literal["consumer", "verifier", "maintainer"]
DEFAULT_ROLE: RoleName = "consumer"

async def get_current_user_id(
    authorization: str = Header(..., description="Bearer <token>"),
) -> str:
    """
    Extracts the JWT token from authorization header and users it to verify user's ID
    """
    # Checks the response is in correct format
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    
    # Removes bearer to get the JWT token
    token = authorization.removeprefix("Bearer ")

    # Creates the client using supabase class Client
    client: Client = get_client()

    try: # Attempts to validate the JWT token with supabase
        user_response = client.auth.get_user(token)
        user = user_response.user
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user.id #This is the user uuid
    except:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user_role(
    user_id: str = Depends(get_current_user_id)
) -> UserRole | None:
    """
    Gets the user_role, depends on previous function to get user_id
    """
    roles=select_by_field(UserRole, "user_id", user_id)
    if roles is not None and len(roles) > 0:
        return roles[0]
    return None


def resolve_role_name(role: UserRole | None) -> RoleName:
    if role is None or role.role is None:
        return DEFAULT_ROLE
    return role.role


async def require_verifier(
    role: UserRole | None = Depends(get_current_user_role)
) -> UserRole:
    """
    Function we can use to limit things to only people with the verifier role
    """
    if resolve_role_name(role) != "verifier" or role is None:
        raise HTTPException(
            status_code=403, detail="Access forbidden: verifier role required"
        )
    return role


async def require_maintainer(
    role: UserRole | None = Depends(get_current_user_role),
) -> UserRole:
    """
    Function we can use to limit things to only people with the maintainer role
    """
    if resolve_role_name(role) != "maintainer" or role is None:
        raise HTTPException(
            status_code=403, detail="Access forbidden: maintainer role required"
        )
    return role
