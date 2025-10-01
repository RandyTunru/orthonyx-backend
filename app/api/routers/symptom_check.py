from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.symptom_check import SymptomCheckIn, SymptomInput, SymptomCheckOut
from app.services.symptoms_check_service import process_symptom_check
from app.db.session import get_session

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def symptom_check(payload: SymptomCheckIn, db: AsyncSession = Depends(get_session)):
    try:
        result = await process_symptom_check(
            db,
            user_id=payload.user_id,
            api_key=payload.api_key,
            age=payload.age,
            sex=payload.sex,
            symptoms=payload.symptoms,
            duration=payload.duration,
            severity=payload.severity,
            additional_notes=payload.additional_notes
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
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