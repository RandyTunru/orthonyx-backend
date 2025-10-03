from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.security import decrypt_api_key
from app.crud.symptom import submit_symptom_check
from app.crud.user import get_user_by_id
from typing import Optional
from app.models.symptoms import SexEnum, StatusEnum
from app.utils.openai_call import open_ai_analysis, OpenAIAuthError, OpenAIRateLimitError, OpenAITransientError, OpenAITimeoutError, OpenAIUnavailableError
import logging

logger = logging.getLogger(__name__)

async def process_symptom_check(db: AsyncSession, user_id : str, api_key: str, age: int, sex: str, symptoms: str, duration: str, severity: int, additional_notes: Optional[str] = None):
    # Decrypt and validate API key 
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

    # Call OpenAI for analysis
    try:
        analysis_text = await open_ai_analysis(age, sex, symptoms, duration, severity, additional_notes)
    except OpenAIAuthError as e:
        # Serious config issue (bad server API key)
        logger.exception("OpenAI authentication error — check server OPENAI_API_KEY")
        symptom_check.analysis = "Analysis temporarily unavailable (server configuration)."
        symptom_check.status = StatusEnum.not_completed
        # persist note so admins can detect, while keeping user data safe
        await db.commit()
        await db.refresh(symptom_check)
        raise e  

    except OpenAIRateLimitError as e:
        # Upstream rate limit
        logger.warning("OpenAI rate-limit: %s", e)
        symptom_check.analysis = "Analysis delayed due to service load; please check back shortly."
        symptom_check.status = StatusEnum.not_completed
        await db.commit()
        await db.refresh(symptom_check)
        raise e  

    except (OpenAITransientError, OpenAITimeoutError, OpenAIUnavailableError) as e:
        # Network/server issues:
        logger.warning("OpenAI transient/unavailable: %s", e)
        # Simple heuristic fallback (not diagnostic): echo input as minimal analysis
        heuristic = f"Unable to complete automated analysis. Patient reports: {symptoms[:300]}."
        symptom_check.analysis = heuristic
        symptom_check.status = StatusEnum.not_completed
        await db.commit()
        await db.refresh(symptom_check)
        raise e

    except Exception as e:
        # Catch-all
        logger.exception("Unexpected error while calling OpenAI: %s", e)
        symptom_check.analysis = "Analysis currently unavailable."
        symptom_check.status = StatusEnum.not_completed
        await db.commit()
        await db.refresh(symptom_check)
        raise e
    
    symptom_check.analysis = analysis_text
    symptom_check.status = StatusEnum.completed

    await db.commit()
    await db.refresh(symptom_check)

    return symptom_check