# app/services/symptoms_check_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.security import decrypt_api_key
from app.crud.symptom import submit_symptom_check, update_symptom_analysis
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
    
    # Submit symptom check. Note we do NOT commit here.
    # It's part of the overall transaction.
    symptom_check = await submit_symptom_check(
        db, user_id=user.id, age=age, sex=SexEnum(sex), symptoms=symptoms,
        duration=duration, severity=severity, additional_notes=additional_notes
    )
    # The `await db.flush()` in `submit_symptom_check` makes the ID available
    # without needing a commit.
    symptom_check_id = symptom_check.id

    # Call OpenAI for analysis
    try:
        analysis_text = await open_ai_analysis(age, sex, symptoms, duration, severity, additional_notes)
        final_status = StatusEnum.completed
    except OpenAIAuthError as e:
        logger.exception("OpenAI authentication error — check server OPENAI_API_KEY")
        analysis_text = "Analysis temporarily unavailable (server configuration)."
        final_status = StatusEnum.not_completed
        # We still update the record within the same transaction before re-raising
        await update_symptom_analysis(db, symptom_check_id, analysis_text, final_status)
        raise e
    except OpenAIRateLimitError as e:
        logger.warning("OpenAI rate-limit: %s", e)
        analysis_text = "Analysis delayed due to service load; please check back shortly."
        final_status = StatusEnum.not_completed
        await update_symptom_analysis(db, symptom_check_id, analysis_text, final_status)
        raise e
    except (OpenAITransientError, OpenAITimeoutError, OpenAIUnavailableError) as e:
        logger.warning("OpenAI transient/unavailable: %s", e)
        heuristic = f"Unable to complete automated analysis. Patient reports: {symptoms[:300]}."
        analysis_text = heuristic
        final_status = StatusEnum.not_completed
        await update_symptom_analysis(db, symptom_check_id, analysis_text, final_status)
        raise e
    except Exception as e:
        logger.exception("Unexpected error while calling OpenAI: %s", e)
        analysis_text = "Analysis currently unavailable."
        final_status = StatusEnum.not_completed
        await update_symptom_analysis(db, symptom_check_id, analysis_text, final_status)
        raise e

    #placeholder
    # analysis_text = "Placeholder analysis text."
    # final_status = StatusEnum.completed
    
    # Update symptom check with analysis if OpenAI call was successful
    updated_symptom_check = await update_symptom_analysis(db, symptom_check_id, analysis_text, final_status)
    await db.commit()
    await db.refresh(updated_symptom_check)
    
    return updated_symptom_check