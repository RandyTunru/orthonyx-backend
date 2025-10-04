from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.symptom_check import SymptomCheckIn, SymptomInput, SymptomCheckOut
from app.services.symptoms_check_service import process_symptom_check
from app.db.session import get_session
from app.schemas.authenticated_user import AuthenticatedUser
from app.api.dependencies import get_current_user, RedisTokenBucketRateLimiter
from app.exceptions.openai_exceptions import OpenAIError

router = APIRouter()

symptom_check_rate_limiter = RedisTokenBucketRateLimiter(capacity=5, refill_rate=1/12, endpoint="post_symptom_check")  # 5 requests per minute

@router.post("/", status_code=status.HTTP_201_CREATED, dependencies=[Depends(symptom_check_rate_limiter)])
async def symptom_check(payload: SymptomCheckIn, current_user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    try:
        result = await process_symptom_check(
            db,
            user_id=current_user.id,
            api_key=current_user.api_key,
            age=payload.age,
            sex=payload.sex,
            symptoms=payload.symptoms,
            duration=payload.duration,
            severity=payload.severity,
            additional_notes=payload.additional_notes
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except OpenAIError as e:
        raise HTTPException(status_code=502, detail=f"Upstream OpenAI error: {str(e)}")
    
    SymptomInput(
        age=result.age,
        sex=result.sex,
        symptoms=result.symptoms,
        duration=result.duration,
        severity=result.severity,
        additional_notes=result.additional_notes
    )

    return SymptomCheckOut(
        id=str(result.id),
        user_id=str(result.user_id),
        timestamp=result.submitted_at,
        input=SymptomInput(
            age=result.age,
            sex=result.sex,
            symptoms=result.symptoms,
            duration=result.duration,
            severity=result.severity,
            additional_notes=result.additional_notes
        ),
        analysis=result.analysis,
        status=result.status
    )