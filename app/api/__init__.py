from fastapi import APIRouter
from .routers import auth, symptom_check

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(symptom_check.router, prefix="/symptom-check", tags=["symptom-check"])

__all__ = ["api_router"]