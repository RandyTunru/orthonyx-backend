from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.security import decrypt_api_key
from app.crud.symptom import get_symptom_checkby_user_id
from app.crud.user import get_user_by_id

async def get_symptom_history(db: AsyncSession, user_id: str, api_key: str):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise ValueError("invalid_user")
    
    raw_api_key = decrypt_api_key(user.api_key_enc)
    if raw_api_key != api_key:
        raise ValueError("invalid_api_key")

    symptom_history = await get_symptom_checkby_user_id(db, user_id=user.id, limit=10, offset=0)
    return symptom_history
