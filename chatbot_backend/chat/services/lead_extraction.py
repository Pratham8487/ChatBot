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


def _infer_intent_from_stage(stage: str, extracted_intent: str | None) -> str | None:
    """
    Infer intent_level based on conversation stage if not explicitly extracted.
    
    Stage progression = increasing user intent:
    - greeting: low intent (just starting conversation)
    - discovery: low-medium intent (understanding problems)
    - qualification: medium intent (evaluating benefits)
    - contact: medium-high intent (ready for next steps, providing contact)
    - closing: high intent (scheduling, confirming details, ready to proceed)
    
    This follows real-world sales funnel behavior where stage progression itself
    indicates growing commitment.
    """
    # If LLM explicitly extracted an intent, use that first
    if extracted_intent in {"low", "medium", "high"}:
        return extracted_intent
    
    # Otherwise, infer from stage (stage progression = commitment)
    stage_intent_map = {
        "greeting": "low",
        "discovery": "low",
        "qualification": "medium",
        "contact": "medium",
        "closing": "high"
    }
    
    inferred = stage_intent_map.get(stage.lower(), None)
    logger.info(f"[Lead Extraction] Inferred intent_level='{inferred}' from stage='{stage}' (extracted: {extracted_intent})")
    
    return inferred


def extract_lead_from_message(
    user_message: str, 
    engine: str = "ollama",
    conversation_stage: str | None = None
) -> LeadData:
    """
    Uses LLM to extract structured lead data from a user message.
    
    Also infers intent_level from conversation stage if not explicitly detected.
    This provides context-aware lead qualification that matches real-world sales funnel behavior.

    This function is hardened against:
    - Non-JSON LLM output
    - Extra text before/after JSON
    - Partial or missing fields
    - Missing intent_level (inferred from stage)
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
        extracted = {}

    # 🔹 Normalize intent_level with stage-based inference
    extracted_intent = extracted.get("intent_level")
    intent_level = _infer_intent_from_stage(
        conversation_stage or "greeting",
        extracted_intent
    )

    return LeadData(
        name=extracted.get("name"),
        email=extracted.get("email"),
        phone=extracted.get("phone"),
        company=extracted.get("company"),
        problem=extracted.get("problem"),
        intent_level=intent_level,
    )
