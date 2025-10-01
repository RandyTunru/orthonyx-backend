from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.symptom_history import SymptomHistoryOut, SymptomCheckOut, SymptomInput 
from app.services.symptoms_history_services import get_symptom_history
from app.db.session import get_session
from app.api.dependencies import get_current_user
from app.schemas.authenticated_user import AuthenticatedUser

router = APIRouter()
@router.get("/", status_code=status.HTTP_200_OK)
async def symptom_history(current_user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    try:
        result = await get_symptom_history(
            db,
            user_id=current_user.id,
            api_key=current_user.api_key
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    history = []
    for item in result:
        history.append(
            SymptomCheckOut(
                id=str(item.id),
                user_id=str(item.user_id),
                timestamp=item.submitted_at,
                input=SymptomInput(
                    age=item.age,
                    sex=item.sex,
                    symptoms=item.symptoms,
                    duration=item.duration,
                    severity=item.severity,
                    additional_notes=item.additional_notes
                ),
                analysis=item.analysis,
                status=item.status
            )
        )

    return SymptomHistoryOut(
        user_id=current_user.id,
        history=history
        )