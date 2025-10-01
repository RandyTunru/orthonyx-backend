from fastapi import Header, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.crud.user import get_user_by_id
from app.utils.security import decrypt_api_key
from app.schemas.authenticated_user import AuthenticatedUser

async def get_current_user(
    # Use Header to extract values from the request headers
    user_id: str = Header(..., description="The User's unique ID"),
    api_key: str = Header(..., description="The User's API Key"),
    db: AsyncSession = Depends(get_session)
) -> AuthenticatedUser:
   
    user = await get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    try:
        raw_api_key = decrypt_api_key(user.api_key_enc)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not process credentials",
        )

    if raw_api_key != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )

    return AuthenticatedUser(id=str(user.id), api_key=api_key)