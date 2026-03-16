"""
Chat API view — the single HTTP entry point for the chatbot.

=== WHAT CHANGED ===

BEFORE (old flow):
  1. views.py parses request
  2. orchestrate_conversation() does keyword matching → stuck at "discovery"
  3. generate_llm_response() sends ONLY current message (no history)
  4. extract_lead_from_message() makes a SECOND LLM call
  5. Two LLM calls, no memory, keyword-based stage transitions

AFTER (new flow with LangChain agent):
  1. views.py parses request (same)
  2. invoke_agent() does EVERYTHING in a single call:
     - Loads full conversation history from DB
     - LLM reasons about stage transitions (replaces keyword matching)
     - LLM extracts lead info inline (replaces second LLM call)
     - LLM generates contextual response (with full history)
  3. views.py saves results to DB (same)

=== WHY THE VIEW IS THINNER NOW ===

The old view had 9 steps with manual orchestration. The new view has 6 steps
because the agent handles orchestration, response generation, and lead
extraction internally. The view just does I/O: parse request, call agent,
save to DB, return response.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError

import json
import time
import logging

from utils.message import ERROR_MESSAGES
from chat.models import Lead, Conversation, Message
from chat.services.langchain_agent import invoke_agent

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
@transaction.atomic
def chat_api(request):
    """
    POST /api/chat/?engine=openai|ollama|lmstudio

    Request body:
      { "session_id": "abc-123", "data": "Hello, I need help with..." }

    Response:
      {
        "isSuccess": true,
        "data": {
          "engine": "openai",
          "stage": "discovery",
          "duration": 2.45,
          "response": "Thanks for reaching out! What kind of help are you looking for?",
          "lead": { "qualified": false, "intent_level": "low", "email": null, "phone": null }
        },
        "error": null
      }
    """
    engine = request.GET.get("engine", "ollama").lower()
    logger.info(f"[chat_api] Engine: {engine}")

    try:
        # ------------------------------------------------------------------
        # STEP 1: Parse and validate request
        # ------------------------------------------------------------------
        request_body = json.loads(request.body)
        session_id = request_body.get("session_id")
        user_input = request_body.get("data")

        if not session_id:
            return JsonResponse({
                "isSuccess": False, "data": None,
                "error": "session_id is required"
            }, status=400)

        if not user_input:
            return JsonResponse({
                "isSuccess": False, "data": None,
                "error": ERROR_MESSAGES["MISSING_MESSAGE"]
            }, status=400)

        user_message = user_input if isinstance(user_input, str) else json.dumps(user_input)

        # ------------------------------------------------------------------
        # STEP 2: Get or create conversation
        # ------------------------------------------------------------------
        # The conversation model tracks session_id → stage mapping.
        # On first message, stage defaults to "greeting".
        conversation, created = Conversation.objects.get_or_create(
            session_id=session_id,
            defaults={"stage": "greeting", "channel": "website"}
        )
        if created:
            logger.info(f"[chat_api] New conversation: {session_id}")

        # ------------------------------------------------------------------
        # STEP 3: Save user message BEFORE agent invocation
        # ------------------------------------------------------------------
        # WHY before: The agent's get_conversation_history tool reads from DB.
        # The current message must be saved so the agent can see it in context
        # if it calls that tool. The _load_chat_history() in langchain_agent.py
        # excludes this last message to avoid duplication (it's passed as
        # HumanMessage directly).
        Message.objects.create(
            conversation=conversation,
            role="user",
            content=user_message,
        )

        # ------------------------------------------------------------------
        # STEP 4: Invoke the LangChain agent
        # ------------------------------------------------------------------
        # This single call replaces the old:
        #   - orchestrate_conversation()     → agent calls detect_stage tool
        #   - get_prompt_for_stage()         → dynamic system prompt in agent
        #   - generate_llm_response()        → agent generates response
        #   - extract_lead_from_message()    → agent calls extract_lead_info
        start_time = time.time()

        agent_result = invoke_agent(
            session_id=session_id,
            user_message=user_message,
            current_stage=conversation.stage,
            engine=engine,
        )

        bot_response = agent_result.response
        next_stage = agent_result.stage
        lead_data = agent_result.lead
        qualified = lead_data.is_qualified()

        duration = round(time.time() - start_time, 2)
        logger.info(
            f"[chat_api] Agent responded in {duration}s | "
            f"stage: {conversation.stage} → {next_stage} | "
            f"qualified: {qualified}"
        )

        # ------------------------------------------------------------------
        # STEP 5: Save bot response + update lead + update stage
        # ------------------------------------------------------------------
        Message.objects.create(
            conversation=conversation,
            role="bot",
            content=bot_response,
        )

        # Save/update lead if contact info was extracted
        lead = None
        try:
            if lead_data.email:
                lead, lead_created = Lead.objects.get_or_create(
                    email=lead_data.email,
                    defaults={"source": "website"}
                )
                logger.info(f"[chat_api] Lead {'created' if lead_created else 'updated'}: {lead_data.email}")

            elif lead_data.phone:
                lead, lead_created = Lead.objects.get_or_create(
                    phone=lead_data.phone,
                    defaults={"source": "website"}
                )
                logger.info(f"[chat_api] Lead {'created' if lead_created else 'updated'}: {lead_data.phone}")

            if lead:
                lead.name = lead_data.name or lead.name
                lead.company = lead_data.company or lead.company
                lead.problem = lead_data.problem or lead.problem
                lead.intent_level = lead_data.intent_level or lead.intent_level
                lead.qualified = qualified
                lead.save()
                conversation.lead = lead

        except ValidationError as e:
            logger.error(f"[chat_api] Lead validation error: {e}")
        except Exception as e:
            logger.error(f"[chat_api] Lead save error: {e}")

        # Update conversation stage
        conversation.stage = next_stage
        conversation.save()

        # ------------------------------------------------------------------
        # STEP 6: Return JSON response
        # ------------------------------------------------------------------
        return JsonResponse({
            "isSuccess": True,
            "data": {
                "engine": engine,
                "stage": next_stage,
                "duration": duration,
                "response": bot_response,
                "lead": {
                    "qualified": qualified,
                    "intent_level": lead_data.intent_level,
                    "email": lead_data.email,
                    "phone": lead_data.phone,
                }
            },
            "error": None,
        })

    except json.JSONDecodeError:
        return JsonResponse({
            "isSuccess": False, "data": None,
            "error": "Invalid JSON in request body"
        }, status=400)

    except ValueError as e:
        logger.error(f"[chat_api] ValueError: {e}")
        return JsonResponse({
            "isSuccess": False, "data": None,
            "error": str(e)
        }, status=400)

    except Exception:
        logger.exception("[chat_api] Unexpected error")
        return JsonResponse({
            "isSuccess": False, "data": None,
            "error": ERROR_MESSAGES["LLM_INTERNAL_ERROR"]
        }, status=500)
