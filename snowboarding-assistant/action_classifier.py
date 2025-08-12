import logging
import time
from typing import Dict, Any

from prompts import get_prompt

logger = logging.getLogger(__name__)


def _retry_chat_completion(groq_client, messages, model: str, temperature: float = 0.1, max_retries: int = 3):
    last_error = None
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                time.sleep(2 ** attempt)
            return groq_client.chat.completions.create(
                messages=messages,
                model=model,
                temperature=temperature,
            )
        except Exception as exc:
            last_error = exc
            logger.warning(f"Action classifier attempt {attempt + 1} failed: {exc}")
    # Exhausted retries
    if last_error:
        raise last_error


def classify_actions(
    user_prompt: str,
    groq_client,
    model: str,
) -> Dict[str, Any]:
    """
    Call the LLM-based action classifier and return a structured result.

    Returns a dict:
      {
        "tool_use": {"search": bool, "geolocation": bool},
        "search_query": str | None,
        "raw_response": str
      }
    """
    system_prompt = get_prompt("action_classifier")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    completion = _retry_chat_completion(
        groq_client=groq_client,
        messages=messages,
        model=model,
        temperature=0.1,
    )

    raw = completion.choices[0].message.content.strip()
    upper = raw.upper()

    tool_use = {"search": False, "geolocation": False}
    search_query = None

    if "SEARCH" in upper:
        tool_use["search"] = True
    elif "GEO" in upper:
        tool_use["geolocation"] = True

    return {
        "tool_use": tool_use,
        "search_query": search_query,
        "raw_response": raw,
    }

