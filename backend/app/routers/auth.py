from fastapi import APIRouter, Depends
from app.middleware.auth import get_current_user
from app.models.user import FirebaseUser

router = APIRouter()


@router.get("/me")
async def me(user: FirebaseUser = Depends(get_current_user)):
    """Return the current authenticated user's profile."""
    return {
        "uid": user.uid,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
    }
