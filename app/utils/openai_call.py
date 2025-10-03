import json
import asyncio
import logging
from typing import Optional, Dict, Any

from openai import (
    AsyncOpenAI,
    APIError,
    APIConnectionError,
    RateLimitError,
    APITimeoutError,
    AuthenticationError,
    OpenAIError,
)

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, RetryError

from app.exceptions.openai_exceptions import (
    OpenAIAuthError,
    OpenAIRateLimitError,
    OpenAITransientError,
    OpenAITimeoutError,
    OpenAIUnavailableError,
)

from app.core.openai_config import openai_settings

logger = logging.getLogger(__name__)

OPENAI_API_KEY = openai_settings.OPENAI_API_KEY
OPENAI_MODEL = openai_settings.OPENAI_MODEL
OPENAI_MAX_CONCURRENCY = openai_settings.OPENAI_MAX_CONCURRENCY
OPENAI_TIMEOUT_SEC = openai_settings.OPENAI_TIMEOUT_SEC

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Semaphore: local concurrency limit per-process
_SEMAPHORE = asyncio.Semaphore(OPENAI_MAX_CONCURRENCY)

# Tenacity retry conditions
retry_on = (
    retry_if_exception_type(APIConnectionError)
    | retry_if_exception_type(APIError)
    | retry_if_exception_type(RateLimitError)
    | retry_if_exception_type(APITimeoutError)
)

@retry(
    reraise=True,
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_on,
)
async def _call_openai_chat(messages: list[dict], model: str, timeout: int = 30) -> Any:
    """
    Low-level OpenAI chat call with retries for transient errors.
    """
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            max_tokens=600,
            timeout=timeout,
        )
        return resp
    except AuthenticationError as e:
        # Auth error, will not be retryable
        logger.exception("OpenAI authentication failed")
        raise 
    except RateLimitError as e:
        # let tenacity retry this; if it still fails it'll propagate here after retries exhausted
        logger.warning("OpenAI rate limit error (will be retried by decorator): %s", e)
        raise
    except APITimeoutError as e:
        logger.warning("OpenAI request timed out: %s", e)
        raise
    except (APIConnectionError, APIError) as e:
        logger.warning("OpenAI transient/API error (will be retried): %s", e)
        raise
    except OpenAIError as e:
        logger.exception("Unexpected OpenAI SDK error")
        raise OpenAIUnavailableError("OpenAI service error") from e

async def open_ai_analysis(
    age: int,
    sex: str,
    symptoms: str,
    duration: str,
    severity: int,
    additional_notes: Optional[str] = None,
    model: Optional[str] = None,
    acquire_timeout: Optional[float] = None,
) -> str:
    """
    Return a plain-text analysis from OpenAI.
    """
    model = model or OPENAI_MODEL
    acquire_timeout = acquire_timeout if acquire_timeout is not None else OPENAI_TIMEOUT_SEC

    system_msg = {
        "role": "system",
        "content": (
            """
                You are an AI clinical assistant. Your purpose is to provide a helpful, preliminary analysis of patient symptoms. Your tone should be knowledgeable, reassuring, and clear.

                Based on the patient data provided, you MUST generate a response formatted into these exact four sections:

                # Potential Conditions
                Confidently list 1-3 of the most probable conditions that match the symptoms, starting with the most likely. For each condition, provide a very brief (1-sentence) rationale. Frame these as possibilities for discussion with a healthcare professional.

                # Explanation
                In a concise paragraph, explain why these conditions are plausible based on the combination of symptoms, severity, and duration provided. If certain symptoms point more strongly to one condition over others, mention it here.

                # Recommended Next Steps
                Provide a clear, actionable list of next steps. This should include:
                - Suggestions for at-home symptom management (e.g., rest, hydration, over-the-counter medications).
                - Specific signs or "red flags" that should prompt the user to see a doctor immediately (e.g., "if the fever exceeds 103°F / 39.4°C").
                - General advice to consult a healthcare professional for an accurate diagnosis.

                # Disclaimer
                Conclude your entire response with this exact, unmodified disclaimer: "Disclaimer: I am an AI assistant and not a medical professional. This analysis is for informational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or another qualified health provider with any questions you may have regarding a medical condition."

                If the provided symptoms are too vague or insufficient to form a reasonable list of potential conditions, you must state that and ask specific clarifying questions to get the necessary information.
            """
        ),
    }

    user_payload = {
        "age": age,
        "sex": sex,
        "symptoms": symptoms,
        "duration": duration,
        "severity": severity,
        "additional_notes": additional_notes or "",
    }
    user_msg = {
        "role": "user",
        "content": f"Patient data:\n{json.dumps(user_payload, ensure_ascii=False)}\n\nProvide a concise plain-text analysis.",
    }

    # Acquire semaphore with timeout so callers can fail fast if system is overloaded
    try:
        await asyncio.wait_for(_SEMAPHORE.acquire(), timeout=acquire_timeout)
    except asyncio.TimeoutError as e:
        logger.warning("Too many concurrent OpenAI requests; semaphore acquire timed out")
        raise OpenAITransientError("Too many concurrent OpenAI requests; try again later") from e

    try:
        try:
            resp = await _call_openai_chat([system_msg, user_msg], model=model, timeout=30)
        except RateLimitError as e:
            logger.warning("OpenAI rate limit exhausted after retries")
            raise OpenAIRateLimitError("OpenAI rate limit reached") from e
        except APITimeoutError as e:
            raise OpenAITimeoutError("OpenAI timeout") from e
        except AuthenticationError as e:
            raise OpenAIAuthError("OpenAI authentication failed") from e
        except (APIConnectionError, APIError) as e:
            raise OpenAITransientError("OpenAI transient error") from e
        except RetryError as e:
            logger.exception("OpenAI retries exhausted: %s", e)
            raise OpenAIUnavailableError("OpenAI retries exhausted") from e

        try:
            content = resp.choices[0].message.content
            analysis_text = str(content).strip()
        except Exception:
            try:
                resp_dict = resp.to_dict() if hasattr(resp, "to_dict") else dict(resp)
                analysis_text = resp_dict["choices"][0]["message"]["content"]
            except Exception:
                logger.exception("Unexpected OpenAI response shape: %s", resp)
                raise OpenAIUnavailableError("Invalid response from OpenAI")

        if not analysis_text:
            logger.warning("OpenAI returned empty content; using fallback text")
            return "Analysis unavailable at the moment; please try again later."

        return analysis_text

    finally:
        _SEMAPHORE.release()
