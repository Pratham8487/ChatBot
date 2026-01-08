import json
import logging
import re

from .lead_models import LeadData
from chat.utils import generate_llm_response

logger = logging.getLogger(__name__)


def _safe_json_extract(text: str) -> dict | None:
    """
    Safely extract the first valid JSON object from LLM output.
    This protects against extra text, explanations, or formatting noise.
    """
    try:
        # Find all potential JSON blocks and try to parse them
        # Start from the first '{' and try progressively longer strings until we find valid JSON
        start_idx = text.find('{')
        if start_idx == -1:
            return None
        
        # Try to find matching closing brace by attempting to parse
        brace_count = 0
        for i, char in enumerate(text[start_idx:], start=start_idx):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    # Try to parse this substring as JSON
                    candidate = text[start_idx:i+1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        # Continue looking for next valid JSON
                        continue
        
        return None
    except Exception as e:
        logger.error(f"[Lead Extraction] JSON extraction error: {e}")
        return None


def extract_lead_from_message(user_message: str, engine: str = "ollama") -> LeadData:
    """
    Uses LLM to extract structured lead data from a user message.

    This function is hardened against:
    - Non-JSON LLM output
    - Extra text before/after JSON
    - Partial or missing fields
    """

    # 🔹 Call LLM extraction prompt
    result = generate_llm_response(
        data=user_message,
        prompt="extract",
        file_name="lead_extract",
        engine=engine
    )

    raw_output = result.get("summary", "")
    logger.debug(f"[Lead Extraction Raw Output] {raw_output}")

    # 🔹 Safe JSON parsing (CRITICAL FIX)
    extracted = _safe_json_extract(raw_output)

    if not extracted:
        logger.warning("Failed to parse lead extraction JSON. Returning empty LeadData.")
        logger.error("[Lead Extraction] Extraction failed — invalid JSON from LLM")
        extracted = {}
        return LeadData()

    # 🔹 Normalize intent_level (extra safety)
    intent_level = extracted.get("intent_level")
    if intent_level not in {"low", "medium", "high"}:
        intent_level = None

    return LeadData(
        name=extracted.get("name"),
        email=extracted.get("email"),
        phone=extracted.get("phone"),
        company=extracted.get("company"),
        problem=extracted.get("problem"),
        intent_level=intent_level,
    )
