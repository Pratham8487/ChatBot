from chat.services.langgraph_state import ConversationState
from chat.services.lead_extraction import extract_lead_from_message


def extract_lead_node(state: ConversationState) -> ConversationState:
    """
    Extract structured lead information from the user's message
    if extraction is required.
    """

    if not state.should_extract_lead:
        return state  # Skip extraction safely

    user_message = state.user_message

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

    return state
