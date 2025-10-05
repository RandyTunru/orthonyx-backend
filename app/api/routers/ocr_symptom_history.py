from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.ocr_symptom_history import OCRSymptomCheckOut, OCRSymptomHistoryOut
from app.schemas.symptom_history import SymptomHistoryOut
from app.services.ocr_symptoms_history_service import ocr_get_symptom_history
from app.db.session import get_session
from app.api.dependencies import get_current_user, RedisTokenBucketRateLimiter
from app.schemas.authenticated_user import AuthenticatedUser


router = APIRouter()

ocr_symptom_history_rate_limiter = RedisTokenBucketRateLimiter(capacity=10, refill_rate=1/6, endpoint="get_symptom_history")  # 10 requests per minute

@router.get("/", status_code=status.HTTP_200_OK, dependencies=[Depends(ocr_symptom_history_rate_limiter)])
async def ocr_symptom_history(current_user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    """ Endpoint to retrieve the symptom history for the authenticated user using OCR-identified data.

        **Note:** This is a protected endpoint that requires authentication. to get an API key and user ID, sign up at POST /auth/signup then login with the credentials at POST /auth/login and use the returned API key and user ID for authentication header.
    """
    try:
        result = await ocr_get_symptom_history(
            db,
            user_id=current_user.id,
            api_key=current_user.api_key
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    history = []
    for item in result:
        history.append(
            OCRSymptomCheckOut(
                id=str(item.id),
                user_id=str(item.user_id),
                timestamp=item.submitted_at,
                input=item.input,
                analysis=item.analysis,
                status=item.status
            )
        )

    return OCRSymptomHistoryOut(
        user_id=current_user.id,
        history=history
        )