from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.security import decrypt_api_key
from app.crud.symptom import submit_symptom_check
from app.crud.user import get_user_by_id
from typing import Optional
from app.models.symptoms import SexEnum, StatusEnum

async def process_symptom_check(db: AsyncSession, user_id : str, api_key: str, age: int, sex: str, symptoms: str, duration: str, severity: int, additional_notes: Optional[str] = None):
    # Decrypt and validate API key (pseudo-code, implement as needed)
    user = await get_user_by_id(db, user_id)
    if not user:
        raise ValueError("invalid_user")
    
    raw_api_key = decrypt_api_key(user.api_key_enc)
    if raw_api_key != api_key:
        raise ValueError("invalid_api_key")
    
    # Submit symptom check
    symptom_check = await submit_symptom_check(
        db,
        user_id=user.id,
        age=age,
        sex=SexEnum(sex),
        symptoms=symptoms,
        duration=duration,
        severity=severity,
        additional_notes=additional_notes
    )

    # Placeholder for analysis logic
    analysis = f"Preliminary analysis for symptoms: ..."
    
    symptom_check.analysis = analysis
    symptom_check.status = StatusEnum.completed

    await db.commit()
    await db.refresh(symptom_check)

    return symptom_check

