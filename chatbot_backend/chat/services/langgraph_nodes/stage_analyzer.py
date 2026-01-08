import logging
from chat.services.langgraph_state import ConversationState

logger = logging.getLogger(__name__)


def analyze_stage_node(state: ConversationState) -> ConversationState:
    """
    Decide the next conversation stage based on:
    - current stage
    - user message
    - lead data
    """
    logger.info(f"[Stage Analyzer] Starting analysis | Current Stage: {state.stage}")

    current_stage = state.stage
    message = state.user_message.lower()

    # Default flags
    state.should_extract_lead = False
    state.should_end_conversation = False

    # ---- STAGE TRANSITIONS ----

    if current_stage == "greeting":
        logger.info(f"[Stage Analyzer] Transition: greeting → discovery")
        state.stage = "discovery"
        state.should_extract_lead = True

    elif current_stage == "discovery":
        # If user shows some intent, move forward
        if state.intent_level in ("medium", "high"):
            logger.info(f"[Stage Analyzer] Intent level {state.intent_level} detected → Moving to qualification")
            state.stage = "qualification"
            state.should_extract_lead = True
        else:
            logger.info(f"[Stage Analyzer] Intent level {state.intent_level} → Staying in discovery")
            state.stage = "discovery"

    elif current_stage == "qualification":
        # If contact info is present, move to contact stage
        email = (state.lead_data or {}).get("email")
        phone = (state.lead_data or {}).get("phone")

        if email or phone:
            logger.info(f"[Stage Analyzer] Contact info found (email={bool(email)}, phone={bool(phone)}) → Moving to contact")
            state.stage = "contact"
            state.should_extract_lead = True
        else:
            logger.info(f"[Stage Analyzer] No contact info yet → Staying in qualification")
            state.stage = "qualification"

    elif current_stage == "contact":
        if state.qualified:
            logger.info(f"[Stage Analyzer] Lead qualified → Moving to closing")
            state.stage = "closing"
        else:
            logger.info(f"[Stage Analyzer] Lead not qualified yet → Staying in contact")
            state.stage = "contact"

    elif current_stage == "closing":
        logger.info(f"[Stage Analyzer] Conversation ending → Moving to exit")
        state.should_end_conversation = True
        state.stage = "exit"

    logger.info(f"[Stage Analyzer] Complete | Final Stage: {state.stage} | Extract Lead: {state.should_extract_lead}")
    return state
