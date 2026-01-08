import logging
from chat.services.langgraph_state import ConversationState

logger = logging.getLogger(__name__)


def stage_updater_node(state: ConversationState) -> ConversationState:
    """
    Decide the FINAL stage after lead extraction.
    """
    logger.info(f"[Stage Updater] Starting | Current Stage: {state.stage} | Intent: {state.intent_level}")

    email = (state.lead_data or {}).get("email")
    phone = (state.lead_data or {}).get("phone")

    if state.intent_level in ("medium", "high"):
        if email or phone:
            logger.info(f"[Stage Updater] High intent + contact info → Setting stage to 'contact' and qualified=True")
            state.stage = "contact"
            state.qualified = True
        else:
            logger.info(f"[Stage Updater] High intent but no contact info → Setting stage to 'qualification'")
            state.stage = "qualification"
    else:
        logger.info(f"[Stage Updater] Intent level {state.intent_level} - no stage change")

    logger.info(f"[Stage Updater] Complete | Final Stage: {state.stage} | Qualified: {state.qualified}")
    return state
