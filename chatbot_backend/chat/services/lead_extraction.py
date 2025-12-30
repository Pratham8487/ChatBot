import json
import logging
from .lead_models import LeadData
from chat.utils import *

logger = logging.getLogger(__name__)


def extract_lead_from_message(user_message: str, engine: str = "ollama") -> LeadData:
    """
    Uses LLM to extract structured lead data from a user message.
    """
    result = generate_llm_response(
        data=user_message,
        prompt="extract",
        file_name="lead_extract",
        engine=engine
    )

    raw_output = result.get("summary", "")

    try:
        extracted = json.loads(raw_output)
    except json.JSONDecodeError:
        logger.warning("Failed to parse lead extraction JSON")
        extracted = {}

    return LeadData(
        name=extracted.get("name"),
        email=extracted.get("email"),
        phone=extracted.get("phone"),
        company=extracted.get("company"),
        problem=extracted.get("problem"),
        intent_level=extracted.get("intent_level"),
    )
