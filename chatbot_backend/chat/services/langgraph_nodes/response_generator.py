import logging
from chat.services.langgraph_state import ConversationState
from chat.utils import generate_llm_response

logger = logging.getLogger(__name__)

STAGE_PROMPT_MAP = {
    "greeting": "greeting",
    "discovery": "discovery",
    "qualification": "qualification",
    "contact": "contact",
    "closing": "closing",
}


def generate_response_node(state: ConversationState) -> ConversationState:
    """
    Generate the chatbot response based on the current conversation stage.
    """
    logger.info(f"[Response Generator] Starting | Stage: {state.stage}")

    stage = state.stage
    user_message = state.user_message

    # Fallback safety
    prompt_name = STAGE_PROMPT_MAP.get(stage, "discovery")
    logger.info(f"[Response Generator] Using prompt: {prompt_name}")

    result = generate_llm_response(
        data=user_message,
        prompt="lead",
        file_name=prompt_name,
        engine=state.metadata.get("engine", "ollama") if state.metadata else "ollama"
    )

    state.bot_response = result.get("summary", "").strip()
    logger.info(f"[Response Generator] Complete | Response length: {len(state.bot_response)} chars")

    return state
