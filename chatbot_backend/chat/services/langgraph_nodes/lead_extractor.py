import logging
from chat.services.langgraph_state import ConversationState
from chat.services.lead_extraction import extract_lead_from_message

logger = logging.getLogger(__name__)


def extract_lead_node(state: ConversationState) -> ConversationState:
    """
    Extract structured lead information from the user's message
    if extraction is required.
    """
    logger.info(f"[Lead Extractor] Starting | Should Extract: {state.should_extract_lead}")

    if not state.should_extract_lead:
        logger.info(f"[Lead Extractor] Skipped - extraction not required")
        return state  # Skip extraction safely

    user_message = state.user_message
    logger.info(f"[Lead Extractor] Extracting from message: {user_message[:100]}...")

    lead_data = extract_lead_from_message(
        user_message=user_message,
        engine=state.metadata.get("engine", "ollama") if state.metadata else "ollama"
    )

    # Update state
    state.lead_data = {
        "name": lead_data.name,
        "email": lead_data.email,
        "phone": lead_data.phone,
        "company": lead_data.company,
        "problem": lead_data.problem,
    }

    state.intent_level = lead_data.intent_level

    # Qualification rule (business logic)
    state.qualified = bool(
        lead_data.intent_level in ("medium", "high")
        and (lead_data.email or lead_data.phone)
    )

    logger.info(
        f"[Lead Extractor] Complete | "
        f"Intent: {state.intent_level} | "
        f"Email: {bool(lead_data.email)} | "
        f"Phone: {bool(lead_data.phone)} | "
        f"Qualified: {state.qualified}"
    )

    return state
