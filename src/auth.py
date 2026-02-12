from fastapi import Depends, HTTPException, Header
from supabase import Client

from .database import get_client, select_by_field
from .models.user import UserRole

async def get_current_user_id(authorisation: str = Header(..., description="Bearer <token>")) -> str:
    """
    Extracts the JWT token from authorisation header and users it to verify user's ID
    """
    # Checks the response is in correct format
    if not authorisation.startswith("Bearer"):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    
    # Removes bearer to get the JWT token
    token = authorisation.removeprefix("Bearer ")
    
    # Creates the client using supabase class Client
    client: Client = get_client()
    
    try: # Attempts to validate the JWT token with supabase
        user_reponse = client.auth.get_user(token)
        user = user_reponse.user
        if user is None: 
            return HTTPException(status_code=401, detail="Invalid token")
        return user.id #This is the user uuid
    except:
        return HTTPException(status_code=401, detail="Invalid token")
    
async def get_current_user_role(
    user_id: str = Depends(get_current_user_id)
) -> UserRole | None:
    """
    Gets the user_role, depends on previous function to get user_id
    """
    roles=select_by_field(UserRole, "user_id", user_id)
    if roles is not None:
        return roles[0]
    else:
        return None
    
asy