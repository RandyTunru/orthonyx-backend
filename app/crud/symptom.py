from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.models.symptoms import Symptom, SexEnum, StatusEnum
import uuid

async def submit_symptom_check(
    db: AsyncSession, user_id: uuid.UUID, age: int, sex: SexEnum, 
    symptoms: str, duration: str, severity: int, additional_notes: Optional[str] = None
) -> Symptom:
    """Creates a symptom check object and adds it to the session."""
    symptom_check = Symptom(
        user_id=user_id, age=age, sex=sex, symptoms=symptoms,
        duration=duration, severity=severity, additional_notes=additional_notes,
        status=StatusEnum.not_completed 
    )
    db.add(symptom_check)
    await db.flush()  # Use flush to get the ID without committing
    return symptom_check

async def update_symptom_analysis(
    db: AsyncSession, symptom_id: uuid.UUID, analysis_text: str, status: StatusEnum
) -> Symptom:
    """Finds a symptom check, updates it, but does NOT commit."""
    result = await db.execute(select(Symptom).where(Symptom.id == symptom_id))
    symptom_check = result.scalar_one()
    
    symptom_check.analysis = analysis_text
    symptom_check.status = status
    
    await db.flush() # Flush to ensure changes are sent to the DB within the transaction
    return symptom_check

async def get_symptom_checkby_user_id(db: AsyncSession, user_id: str, limit: int = 10, offset: int = 0):
    q = select(Symptom).where(Symptom.user_id == user_id).where(Symptom.status == StatusEnum.completed).order_by(Symptom.submitted_at.desc()).limit(limit).offset(offset)
    res = await db.execute(q)
    return res.scalars().all()