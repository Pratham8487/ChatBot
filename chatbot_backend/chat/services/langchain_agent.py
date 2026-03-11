"""
LangChain Agent — Core of the new architecture.

=== WHY THIS FILE EXISTS ===

The old flow had 3 critical problems:

1. STAGE STUCK AT "discovery":
   conversation_orchestrator.py used keyword matching:
     if any(word in message for word in ["need", "problem", "looking", "help"])
   Real users don't speak in these exact keywords, so the stage never advanced.

2. NO CONVERSATION MEMORY:
   views.py sent ONLY the current user message to the LLM:
     generate_llm_response(data=user_message, ...)
   The LLM had zero context about previous turns. Every message was processed
   in isolation, making coherent multi-turn conversation impossible.

3. TWO SEPARATE LLM CALLS per turn:
   - One for generating the response (generate_llm_response)
   - One for extracting lead data (extract_lead_from_message)
   This doubled latency and cost, and the two calls couldn't coordinate.

=== HOW THE LANGCHAIN AGENT SOLVES ALL THREE ===

The agent is a ReAct (Reasoning + Acting) agent that:
  1. Receives the full conversation history (not just current message)
  2. Reasons about which tools to call (detect_stage, extract_lead_info)
  3. Generates a contextual response in a single invocation
  4. Maintains state across turns via LangGraph checkpointer (thread_id = session_id)

=== FLOW ===

  views.py
    └─→ invoke_agent(session_id, user_message, current_stage, engine)
         │
         ├─→ build_agent(engine)
         │    ├─→ get_llm(engine)           # OpenAI or Ollama
         │    ├─→ tools list                 # detect_stage, extract_lead_info, etc.
         │    └─→ create_react_agent(...)    # LangGraph ReAct agent
         │
         ├─→ Load chat history from DB       # Solves Problem #2
         ├─→ Build system prompt with stage   # Dynamic per-stage instructions
         │
         └─→ agent.invoke(messages, config={"thread_id": session_id})
              │
              ├─→ Agent calls detect_stage tool    # Solves Problem #1
              ├─→ Agent calls extract_lead_info     # Solves Problem #3
              └─→ Agent generates response          # Single LLM invocation

=== WHERE THIS IS CALLED FROM ===

  chat/views.py → chat_api() → invoke_agent()
"""

import json
import logging
import os
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from django.conf import settings

from chat.models import Conversation, Message
from .schemas import AgentResponse, LeadInfo
from .agent_tools import (
    detect_stage,
    stay_in_stage,
    extract_lead_info,
    get_conversation_history,
    STAGE_TRANSITION_GUIDE,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# System prompt template
# ---------------------------------------------------------------------------
# WHY a dynamic prompt: Each stage needs different behavior.
# In "greeting" the bot should welcome; in "contact" it should ask for email.
# The old code loaded separate .txt files per stage. We keep that concept but
# embed the stage instructions directly in the system prompt so the agent
# has full context in a single message.

SYSTEM_PROMPT_TEMPLATE = """You are a professional lead generation assistant on a business website.

## Your Conversation Stage: {stage}
{stage_description}

## Stage Advancement Criteria
To advance from "{stage}": {advance_criteria}

## Stage-Specific Prompt
{stage_prompt}

## Tools Available
You have access to these tools — use them as instructed:

1. **get_conversation_history**: Call this FIRST if you need context from prior messages.
   Pass the session_id: "{session_id}"

2. **detect_stage**: Call this to ADVANCE the conversation to the next stage.
   Only call this when the user has met the advancement criteria above.
   Pass: current_stage="{stage}", user_message=<the user's message>, conversation_summary=<your analysis>

3. **stay_in_stage**: Call this to STAY in the current stage.
   Call this when the user has NOT met the advancement criteria.
   Pass: current_stage="{stage}", reason=<why not advancing>

4. **extract_lead_info**: Call this whenever the user reveals personal/business info
   (name, email, phone, company, or describes their problem).
   Only include fields explicitly stated by the user.
   **CRITICAL**: You MUST set intent_level based on the current conversation stage:
     - "low" → greeting or discovery (visitor is just browsing)
     - "medium" → qualification (visitor shows interest)
     - "high" → contact or closing (visitor provides contact info or is ready to proceed)
   A lead becomes QUALIFIED when intent_level="high" AND email or phone is provided.
   So in contact/closing stages, ALWAYS pass intent_level="high".

## Rules
- Always call either detect_stage OR stay_in_stage (exactly one) every turn
- Always call extract_lead_info when the user shares ANY personal/business detail, with the correct intent_level for the current stage
- Ask only ONE question at a time
- Be conversational, helpful, and not pushy
- Do NOT fabricate information the user hasn't provided
- Keep responses concise (2-4 sentences)
"""


def _load_stage_prompt(stage: str) -> str:
    """
    Load the stage-specific prompt template from utils/Prompts/Lead/<stage>.txt

    WHY: Preserves the existing prompt templates the team has already written.
    These templates contain stage-specific instructions (e.g., "do not ask for
    contact details yet" in greeting). Instead of discarding them, we inject
    them into the agent's system prompt.

    Falls back to a generic prompt if the file doesn't exist.
    """
    prompt_path = os.path.join(settings.PROMPTS_DIR, "Lead", f"{stage}.txt")
    try:
        with open(prompt_path, encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.warning(f"[Agent] Stage prompt not found: {prompt_path}")
        return "You are a helpful business assistant. Guide the conversation naturally."


def _build_system_prompt(stage: str, session_id: str) -> str:
    """
    Assemble the full system prompt from template + stage data.

    WHY separate function: Keeps the prompt construction testable and
    decoupled from the agent invocation logic.
    """
    guide = STAGE_TRANSITION_GUIDE.get(stage, {
        "description": "Unknown stage",
        "advance_when": "N/A",
    })

    stage_prompt = _load_stage_prompt(stage)

    return SYSTEM_PROMPT_TEMPLATE.format(
        stage=stage,
        stage_description=guide["description"],
        advance_criteria=guide["advance_when"],
        stage_prompt=stage_prompt,
        session_id=session_id,
    )


# ---------------------------------------------------------------------------
# LLM factory
# ---------------------------------------------------------------------------

def get_llm(engine: str):
    """
    Create the appropriate LangChain LLM wrapper based on engine selection.

    WHY LangChain wrappers instead of raw API calls:
      - The old generate_with_openai() / generate_with_ollama() functions returned
        raw text strings. LangChain wrappers return Message objects that the agent
        framework can reason about, including tool call instructions.
      - The agent needs the LLM to support tool calling (function calling).
        ChatOpenAI and ChatOllama both support this natively.

    SUPPORTED ENGINES:
      - "openai": Uses ChatOpenAI → calls OpenAI API (gpt-4, gpt-3.5-turbo, etc.)
      - "ollama": Uses ChatOllama → calls local Ollama server
      - "lmstudio": Uses ChatOpenAI with custom base_url → calls LM Studio's
                     OpenAI-compatible endpoint

    WHERE: Called by build_agent() to create the model for the ReAct agent.
    """
    if engine == "openai":
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured in .env")

        model_name = getattr(settings, "LLM_MODEL_OPEN_AI", None) or "gpt-4o-mini"
        logger.info(f"[Agent] Using OpenAI model: {model_name}")

        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            temperature=0.3,
        )

    elif engine == "ollama":
        # Import here to avoid hard dependency if ollama isn't installed
        from langchain_ollama import ChatOllama

        model_name = settings.LLM_MODEL_NAME or "llama3"
        base_url = settings.LLM_LOCAL_API_BASE or "http://localhost:11434"
        logger.info(f"[Agent] Using Ollama model: {model_name} at {base_url}")

        return ChatOllama(
            model=model_name,
            base_url=base_url,
            temperature=0.3,
        )

    elif engine == "lmstudio":
        # LM Studio exposes an OpenAI-compatible API, so we use ChatOpenAI
        # with a custom base_url pointing to the local LM Studio server.
        base_url = settings.LLM_LOCAL_API_BASE or "http://localhost:1234"
        model_name = settings.LLM_MODEL_NAME or "local-model"
        logger.info(f"[Agent] Using LM Studio model: {model_name} at {base_url}")

        return ChatOpenAI(
            model=model_name,
            base_url=f"{base_url}/v1",
            api_key="lm-studio",  # LM Studio doesn't need a real key
            temperature=0.3,
        )

    else:
        raise ValueError(
            f"Unsupported engine: '{engine}'. Choose from: openai, ollama, lmstudio"
        )


# ---------------------------------------------------------------------------
# Agent builder
# ---------------------------------------------------------------------------

def build_agent(engine: str, checkpointer=None):
    """
    Construct the LangGraph ReAct agent.

    WHY create_react_agent:
      ReAct (Reasoning + Acting) is the pattern where the LLM:
        1. THINKS about what to do
        2. ACTS by calling a tool
        3. OBSERVES the tool result
        4. Repeats or responds

      This is perfect for our use case because the agent needs to:
        - Analyze the conversation (THINK)
        - Decide stage transitions (ACT via detect_stage)
        - Extract lead info (ACT via extract_lead_info)
        - Generate a response (final output)

    WHY MemorySaver checkpointer:
      LangGraph checkpointers persist the agent's internal state between
      invocations. With thread_id = session_id, the agent "remembers"
      its previous reasoning across HTTP requests. MemorySaver stores
      this in-memory (suitable for dev). For production, swap to
      PostgresSaver for persistence across server restarts.

    Args:
        engine: LLM engine to use ("openai", "ollama", "lmstudio")
        checkpointer: Optional custom checkpointer. Defaults to MemorySaver.
    """
    llm = get_llm(engine)

    tools = [
        detect_stage,
        stay_in_stage,
        extract_lead_info,
        get_conversation_history,
    ]

    if checkpointer is None:
        checkpointer = MemorySaver()

    agent = create_react_agent(
        model=llm,
        tools=tools,
        checkpointer=checkpointer,
    )

    logger.info(f"[Agent] Built ReAct agent with engine={engine}, tools={[t.name for t in tools]}")
    return agent, checkpointer


# ---------------------------------------------------------------------------
# Agent singleton (keeps memory alive across requests)
# ---------------------------------------------------------------------------
# WHY a module-level cache: build_agent() creates a MemorySaver, which stores
# conversation state in-memory. If we create a new agent per request, the
# memory is lost. By caching per engine, the checkpointer persists across
# requests within the same server process.

_agent_cache: dict[str, tuple] = {}


def get_or_build_agent(engine: str):
    """Get a cached agent or build a new one."""
    if engine not in _agent_cache:
        _agent_cache[engine] = build_agent(engine)
    return _agent_cache[engine]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def invoke_agent(
    session_id: str,
    user_message: str,
    current_stage: str,
    engine: str = "openai",
) -> AgentResponse:
    """
    Invoke the LangChain agent for a single conversation turn.

    This is the ONLY function that views.py needs to call. It replaces:
      - orchestrate_conversation()      → agent calls detect_stage tool
      - get_prompt_for_stage()          → dynamic system prompt
      - generate_llm_response()         → agent generates response
      - extract_lead_from_message()     → agent calls extract_lead_info tool

    Args:
        session_id: Unique conversation identifier (becomes thread_id)
        user_message: The user's current message
        current_stage: The conversation stage at the start of this turn
        engine: LLM engine to use ("openai", "ollama", "lmstudio")

    Returns:
        AgentResponse with stage, response text, and lead info

    WHERE CALLED: chat/views.py → chat_api()
    """
    agent, checkpointer = get_or_build_agent(engine)

    # --- Build system prompt with current stage context ---
    system_prompt = _build_system_prompt(current_stage, session_id)

    # --- Load conversation history from DB ---
    # WHY from DB and not from checkpointer alone:
    #   The DB is the source of truth for messages. The checkpointer stores
    #   agent internal state (tool call history, reasoning). We need both:
    #   DB history for the user/bot messages, checkpointer for agent continuity.
    chat_history = _load_chat_history(session_id)

    # --- Invoke the agent ---
    # thread_id links this invocation to the conversation's checkpoint.
    # The agent will see all previous tool calls and reasoning from prior
    # turns with this same thread_id.
    config = {"configurable": {"thread_id": session_id}}

    messages = [
        SystemMessage(content=system_prompt),
        *chat_history,
        HumanMessage(content=user_message),
    ]

    logger.info(
        f"[Agent] Invoking for session={session_id}, stage={current_stage}, "
        f"engine={engine}, history_msgs={len(chat_history)}"
    )

    result = agent.invoke({"messages": messages}, config=config)

    # --- Parse the agent's output ---
    return _parse_agent_result(result, current_stage)


def _load_chat_history(session_id: str) -> list:
    """
    Load conversation messages from the DB as LangChain message objects.

    WHY: The agent needs to see the full conversation to make contextual
    responses. The old code only sent the current message, causing the LLM
    to respond without any context of prior discussion.

    We exclude the LAST user message because it's passed separately as the
    current HumanMessage (to avoid duplication).

    Returns a list of HumanMessage/AIMessage objects.
    """
    try:
        conversation = Conversation.objects.get(session_id=session_id)
        messages = list(
            Message.objects.filter(conversation=conversation)
            .order_by("created_at")
        )

        if not messages:
            return []

        # Exclude the last message (the one we just saved in views.py)
        prior_messages = messages[:-1]

        history = []
        for msg in prior_messages:
            if msg.role == "user":
                history.append(HumanMessage(content=msg.content))
            else:
                history.append(AIMessage(content=msg.content))

        return history

    except Conversation.DoesNotExist:
        return []
    except Exception as e:
        logger.error(f"[Agent] Failed to load chat history: {e}")
        return []


def _parse_agent_result(result: dict, fallback_stage: str) -> AgentResponse:
    """
    Parse the LangGraph agent result into our AgentResponse schema.

    The agent returns a dict with a "messages" key containing all messages
    from the conversation, including:
      - SystemMessage (our prompt)
      - HumanMessage (user input)
      - AIMessage (agent's thinking + tool calls)
      - ToolMessage (tool results)
      - AIMessage (final response)

    We extract:
      1. The final AI text response (last AIMessage with content)
      2. Stage decision (from detect_stage/stay_in_stage tool results)
      3. Lead info (from extract_lead_info tool results)

    WHY this parsing: LangGraph returns raw message lists. We need to
    extract structured data from tool call results and the final response
    to build the API response.
    """
    all_messages = result.get("messages", [])

    # --- Extract the final bot response ---
    # The last AIMessage with non-empty content is the agent's reply to the user.
    bot_response = ""
    for msg in reversed(all_messages):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            bot_response = msg.content
            break

    # If no clean response found, get the last AIMessage with any content
    if not bot_response:
        for msg in reversed(all_messages):
            if isinstance(msg, AIMessage) and msg.content:
                bot_response = msg.content
                break

    # --- Extract stage decision from tool results ---
    next_stage = fallback_stage
    for msg in all_messages:
        if isinstance(msg, ToolMessage) and msg.name in ("detect_stage", "stay_in_stage"):
            try:
                data = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                if isinstance(data, dict) and "next_stage" in data:
                    next_stage = data["next_stage"]
                    logger.info(f"[Agent] Stage decision: {data.get('current_stage')} → {next_stage} ({data.get('reasoning', '')})")
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"[Agent] Could not parse stage tool result: {e}")

    # --- Extract lead info from tool results ---
    lead_info = LeadInfo()
    for msg in all_messages:
        if isinstance(msg, ToolMessage) and msg.name == "extract_lead_info":
            try:
                data = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                if isinstance(data, dict):
                    # Merge: later calls override earlier ones (progressive extraction)
                    lead_info = LeadInfo(
                        name=data.get("name") or lead_info.name,
                        email=data.get("email") or lead_info.email,
                        phone=data.get("phone") or lead_info.phone,
                        company=data.get("company") or lead_info.company,
                        problem=data.get("problem") or lead_info.problem,
                        intent_level=data.get("intent_level", lead_info.intent_level),
                    )
                    logger.info(f"[Agent] Lead extracted: {lead_info}")
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"[Agent] Could not parse lead tool result: {e}")

    if not bot_response:
        bot_response = "I'm sorry, I couldn't generate a response. Could you please try again?"
        logger.error("[Agent] No response generated by agent")

    return AgentResponse(
        stage=next_stage,
        response=bot_response,
        lead=lead_info,
    )
