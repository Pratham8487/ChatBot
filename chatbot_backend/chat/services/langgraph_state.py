from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ConversationState:
    # --- Conversation control ---
    session_id: str
    stage: str                 # greeting | discovery | qualification | contact | closing | exit

    # --- User input ---
    user_message: str

    # --- LLM response ---
    bot_response: Optional[str] = None

    # --- Lead data ---
    lead_data: Dict[str, Any] = None
    intent_level: Optional[str] = None
    qualified: bool = False

    # --- Control flags ---
    should_extract_lead: bool = False
    should_end_conversation: bool = False

    # --- Metadata ---
    metadata: Dict[str, Any] = None
