from chat.services.langgraph_state import ConversationState


def analyze_stage_node(state: ConversationState) -> ConversationState:
    """
    Decide the next conversation stage based on:
    - current stage
    - user message
    - lead data
    """

    current_stage = state.stage
    message = state.user_message.lower()

    # Default flags
    state.should_extract_lead = False
    state.should_end_conversation = False

    # ---- STAGE TRANSITIONS ----

    if current_stage == "greeting":
        state.stage = "discovery"
        state.should_extract_lead = True

    elif current_stage == "discovery":
        # If user shows some intent, move forward
        if state.intent_level in ("medium", "high"):
            state.stage = "qualification"
            state.should_extract_lead = True
        else:
            state.stage = "discovery"

    elif current_stage == "qualification":
        # If contact info is present, move to contact stage
        email = (state.lead_data or {}).get("email")
        phone = (state.lead_data or {}).get("phone")

        if email or phone:
            state.stage = "contact"
            state.should_extract_lead = True
        else:
            state.stage = "qualification"

    elif current_stage == "contact":
        if state.qualified:
            state.stage = "closing"
        else:
            state.stage = "contact"

    elif current_stage == "closing":
        state.should_end_conversation = True
        state.stage = "exit"

    return state
