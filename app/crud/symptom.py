from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
from typing import Optional
from app.models.symptoms import Symptom, SexEnum, StatusEnum

async def submit_symptom_check(db: AsyncSession, user_id: int, age: int, sex: SexEnum, symptoms: str, duration: str, severity: int, additional_notes: Optional[str] = None):
    # Implementation for submitting a symptom check
    symptom_check = Symptom(
        user_id=user_id,
        age=age,
        sex=sex,
        symptoms=symptoms,
        duration=duration,
        severity=severity,
        additional_notes=additional_notes
    )
    db.add(symptom_check)
    await db.flush()  # Use flush to get the ID without committing
    return symptom_check

async def get_symptom_checkby_user_id(db: AsyncSession, user_id: str, limit: int = 10, offset: int = 0):
    q = select(Symptom).where(Symptom.user_id == user_id).where(Symptom.status == StatusEnum.completed).order_by(Symptom.submitted_at.desc()).limit(limit).offset(offset)
    res = await db.execute(q)
    return res.scalars().all()