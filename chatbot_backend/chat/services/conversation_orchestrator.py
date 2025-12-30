from enum import Enum


class ConversationStage(str, Enum):
    GREETING = "greeting"
    DISCOVERY = "discovery"
    QUALIFICATION = "qualification"
    CONTACT = "contact"
    CLOSING = "closing"


def determine_next_stage(current_stage: ConversationStage, user_message: str) -> ConversationStage:
    message = user_message.lower()

    if current_stage == ConversationStage.GREETING:
        return ConversationStage.DISCOVERY

    if current_stage == ConversationStage.DISCOVERY:
        if any(word in message for word in ["need", "problem", "looking", "help"]):
            return ConversationStage.QUALIFICATION
        return ConversationStage.DISCOVERY

    if current_stage == ConversationStage.QUALIFICATION:
        if any(word in message for word in ["yes", "sure", "interested"]):
            return ConversationStage.CONTACT
        return ConversationStage.QUALIFICATION

    if current_stage == ConversationStage.CONTACT:
        return ConversationStage.CLOSING

    return current_stage


def get_prompt_for_stage(stage: ConversationStage) -> tuple[str, str]:
    """
    Returns (prompt_category, file_name)
    """
    return "lead", stage.value


def orchestrate_conversation(
    user_message: str,
    current_stage: ConversationStage | None
) -> ConversationStage:
    if not current_stage:
        return ConversationStage.GREETING

    return determine_next_stage(current_stage, user_message)
