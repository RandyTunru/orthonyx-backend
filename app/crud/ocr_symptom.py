from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.models.ocr_symptoms import OCRSymptom, StatusEnum

async def ocr_submit_symptom_check(db: AsyncSession, user_id: int, input: dict):
    # Implementation for submitting a symptom check
    symptom_check = OCRSymptom(
        user_id=user_id,
        input=input
    )
    db.add(symptom_check)
    await db.flush()  # Use flush to get the ID without committing
    return symptom_check

async def ocr_get_symptom_checkby_user_id(db: AsyncSession, user_id: str, limit: int = 10, offset: int = 0):
    q = select(OCRSymptom).where(OCRSymptom.user_id == user_id).where(OCRSymptom.status == StatusEnum.completed).order_by(OCRSymptom.submitted_at.desc()).limit(limit).offset(offset)
    res = await db.execute(q)
    return res.scalars().all()