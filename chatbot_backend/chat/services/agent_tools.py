"""
LangChain structured tools for the lead generation agent.

WHY TOOLS INSTEAD OF KEYWORD MATCHING:
  The old conversation_orchestrator.py used hardcoded keyword lists:
    if any(word in message for word in ["need", "problem", "looking", "help"]):
  This caused the stage to get stuck at "discovery" because real user messages
  rarely contain those exact keywords. Tools let the LLM reason about conversation
  context and make intelligent stage transitions.

WHY THESE SPECIFIC TOOLS:
  1. detect_stage — Replaces determine_next_stage() keyword matching.
     The LLM analyzes the full conversation context and decides stage transitions.

  2. extract_lead_info — Replaces the separate extract_lead_from_message() LLM call.
     Instead of a second LLM call with _safe_json_extract() parsing, the agent
     calls this tool inline and returns structured Pydantic data.

  3. get_conversation_history — Solves the "no memory" problem.
     The old code sent only the current message to the LLM with zero history.
     This tool loads the full conversation from PostgreSQL so the agent has context.

WHERE USED:
  - langchain_agent.py: Passed to create_react_agent() as the tools list.
    The agent decides WHEN to call each tool based on conversation flow.
"""

import logging
from langchain_core.tools import tool
from chat.models import Conversation, Message

logger = logging.getLogger(__name__)

# The linear sales funnel stages in order.
# The agent uses this to know what "forward" and "backward" means.
STAGE_ORDER = ["greeting", "discovery", "qualification", "contact", "closing"]

STAGE_TRANSITION_GUIDE = {
    "greeting": {
        "description": "The visitor just arrived. Welcome them.",
        "advance_when": "The visitor has responded to the greeting and indicated why they're here.",
        "next": "discovery",
    },
    "discovery": {
        "description": "Understanding the visitor's problem or need.",
        "advance_when": "The visitor has clearly described their problem, need, or use case. They've given enough detail to evaluate whether they're a good fit.",
        "next": "qualification",
    },
    "qualification": {
        "description": "Assessing if the visitor is a serious potential customer.",
        "advance_when": "The visitor has shown genuine interest — asking about pricing, timelines, or next steps. They seem ready to move forward.",
        "next": "contact",
    },
    "contact": {
        "description": "Collecting contact information for follow-up.",
        "advance_when": "The visitor has provided at least an email or phone number.",
        "next": "closing",
    },
    "closing": {
        "description": "Wrapping up the conversation.",
        "advance_when": "N/A — this is the final stage.",
        "next": "closing",
    },
}


@tool
def detect_stage(
    current_stage: str,
    user_message: str,
    conversation_summary: str,
) -> dict:
    """Decide whether the conversation should advance to the next stage.

    Call this tool EVERY turn to evaluate stage progression.

    The sales funnel stages are:
      greeting → discovery → qualification → contact → closing

    Args:
        current_stage: The stage at the START of this turn (e.g. "discovery")
        user_message: What the user just said
        conversation_summary: Brief summary of what has been discussed so far

    Returns a dict with:
        current_stage: The stage before this turn
        next_stage: The stage after this turn (same or advanced by one)
        reasoning: Why you made this decision
    """
    # This function body provides DEFAULTS. The real intelligence comes from
    # the LLM agent which sees the tool's docstring + args and decides what
    # values to pass. The agent then interprets the return value.
    #
    # However, since the agent fills in the args and we return structured data,
    # we apply the transition logic here as a guardrail:

    guide = STAGE_TRANSITION_GUIDE.get(current_stage)
    if not guide:
        logger.warning(f"[detect_stage] Unknown stage '{current_stage}', defaulting to greeting")
        return {
            "current_stage": current_stage,
            "next_stage": "greeting",
            "reasoning": f"Unknown stage '{current_stage}', resetting to greeting",
        }

    # The agent will call this tool with its analysis in conversation_summary.
    # We trust the agent's decision to advance or stay based on the guide criteria.
    # The next_stage is determined by the STAGE_TRANSITION_GUIDE map.
    next_stage = guide["next"]

    return {
        "current_stage": current_stage,
        "next_stage": next_stage,
        "reasoning": f"Advanced from {current_stage} to {next_stage}. Criteria: {guide['advance_when']}",
    }


@tool
def stay_in_stage(current_stage: str, reason: str) -> dict:
    """Keep the conversation in the current stage without advancing.

    Call this when the user has NOT met the criteria to advance.
    For example, if the user is still in discovery and hasn't clearly
    described their problem yet.

    Args:
        current_stage: The stage to stay in
        reason: Why the conversation should not advance yet
    """
    return {
        "current_stage": current_stage,
        "next_stage": current_stage,
        "reasoning": f"Staying in {current_stage}: {reason}",
    }


@tool
def extract_lead_info(
    name: str = None,
    email: str = None,
    phone: str = None,
    company: str = None,
    problem: str = None,
    intent_level: str = "low",
) -> dict:
    """Extract and record lead information mentioned by the visitor.

    Call this tool whenever the visitor reveals personal or business details
    during the conversation. Only include fields that were EXPLICITLY stated
    by the visitor — do not guess or infer missing fields.

    IMPORTANT — intent_level MUST be set based on the current conversation stage:
      - "low": Stage is greeting or discovery (visitor is browsing/exploring)
      - "medium": Stage is qualification (visitor shows interest, asks questions)
      - "high": Stage is contact or closing (visitor provides contact info, ready to proceed)

    A lead is considered QUALIFIED when intent_level is "high" AND the visitor
    has provided an email or phone number. So always set intent_level to "high"
    when the visitor is in the contact or closing stage.

    Args:
        name: Visitor's name (if mentioned)
        email: Visitor's email address (if provided)
        phone: Visitor's phone number (if provided)
        company: Visitor's company name (if mentioned)
        problem: Business problem or need described by the visitor
        intent_level: MUST match stage — "low" (greeting/discovery), "medium" (qualification), "high" (contact/closing)
    """
    return {
        "name": name,
        "email": email,
        "phone": phone,
        "company": company,
        "problem": problem,
        "intent_level": intent_level if intent_level in ("low", "medium", "high") else "low",
    }


@tool
def get_conversation_history(session_id: str) -> str:
    """Retrieve the full conversation history for this session.

    Call this tool at the START of processing to understand what has been
    discussed previously. This is critical for multi-turn conversations
    where context from earlier messages affects the current response.

    Args:
        session_id: The unique session identifier for this conversation
    """
    try:
        conversation = Conversation.objects.get(session_id=session_id)
        messages = Message.objects.filter(
            conversation=conversation
        ).order_by("created_at")

        if not messages.exists():
            return "This is a brand new conversation. No previous messages."

        history_lines = []
        for msg in messages:
            role_label = "User" if msg.role == "user" else "Assistant"
            history_lines.append(f"{role_label}: {msg.content}")

        return "\n".join(history_lines)

    except Conversation.DoesNotExist:
        return "This is a brand new conversation. No previous messages."
    except Exception as e:
        logger.error(f"[get_conversation_history] Error: {e}")
        return "Could not retrieve conversation history."
