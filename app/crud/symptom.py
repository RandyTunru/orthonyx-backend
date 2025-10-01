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

async def add_analysis(db: AsyncSession, symptom_check_id: int, analysis: str):
    # Implementation for adding analysis to a symptom check
    q = (
        update(Symptom)
        .where(Symptom.id == symptom_check_id)
        .values(
            analysis=analysis,
            status=StatusEnum.completed
        )
        .returning(Symptom)
    )
    res = await db.execute(q)
    await db.commit()
    return res.scalars().first()