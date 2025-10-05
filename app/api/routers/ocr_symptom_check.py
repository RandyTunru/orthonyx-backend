from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Union

from app.schemas.ocr_symptom_check import OCRSymptomCheckIn, OCRSymptomCheckOut
from app.services.ocr_symptoms_check_service import process_symptom_check
from app.db.session import get_session
from app.schemas.authenticated_user import AuthenticatedUser
from app.api.dependencies import get_current_user, RedisTokenBucketRateLimiter
from app.exceptions.openai_exceptions import OpenAIError

router = APIRouter()

ocr_symptom_check_rate_limiter = RedisTokenBucketRateLimiter(capacity=5, refill_rate=1/12, endpoint="post_symptom_check")  # 5 requests per minute, shared with text-based symptom check

@router.post("/", status_code=status.HTTP_201_CREATED, dependencies=[Depends(ocr_symptom_check_rate_limiter)])
async def ocr_symptom_check(payload: OCRSymptomCheckIn, current_user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    """ Endpoint to process a symptom check request using OCR-identified data.

        **Note:** This is a protected endpoint that requires authentication. to get an API key and user ID, sign up at POST /auth/signup then login with the credentials at POST /auth/login and use the returned API key and user ID for authentication header.
    """
    try:
        identified_data = {
            "age": payload.age,
            "sex": payload.sex,
            **payload.identified_data
        }

        result = await process_symptom_check(
            db,
            user_id=current_user.id,
            api_key=current_user.api_key,
            identified_data=identified_data,   
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except OpenAIError as e:
        raise HTTPException(status_code=502, detail=f"Upstream OpenAI error: {str(e)}")
    
    return OCRSymptomCheckOut(
        id=str(result.id),
        user_id=str(result.user_id),
        timestamp=result.submitted_at,
        input=result.input,
        analysis=result.analysis,
        status=result.status
    )