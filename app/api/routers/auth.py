from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import SignupIn, SigninIn, SigninOut
from app.services.auth_service import register_user, signin_and_rotate_api_key
from app.db.session import get_session

from starlette.responses import Response

router = APIRouter()

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupIn, db: AsyncSession = Depends(get_session)):
    try:
        await register_user(db, payload.email, payload.username, payload.password)
        return Response(status_code=status.HTTP_201_CREATED)
    except ValueError as e:
        # decide specific messages:
        if str(e) == "username_exists":
            raise HTTPException(status_code=400, detail="username already exists")
        if str(e) == "email_exists":
            raise HTTPException(status_code=400, detail="email already exists")
        raise HTTPException(status_code=400, detail="invalid input")

@router.post("/signin", response_model=SigninOut)
async def signin(payload: SigninIn, db: AsyncSession = Depends(get_session)):
    user, raw_api_key = await signin_and_rotate_api_key(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return SigninOut(username=user.username, api_key=raw_api_key)
