from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import BaseParser
from rest_framework.exceptions import ParseError
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
import re
import time
import logging

from utils.message import ERROR_MESSAGES

# App imports
from chat.services.conversation_orchestrator import get_prompt_for_stage, orchestrate_conversation
from chat.utils import *
from chat.services.lead_extraction import extract_lead_from_message
from chat.models import Lead, Conversation, Message
from django.views.decorators.csrf import csrf_exempt



# logger declaration
logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def chat_api(request):
    engine = request.GET.get("engine", "ollama").lower()
    logger.info(f"Engine selected: {engine}")

    try:
        request_body = json.loads(request.body)

        session_id = request_body.get("session_id")
        user_input = request_body.get("data")

        if not session_id:
            return JsonResponse({
                "isSuccess": False,
                "data": None,
                "error": "session_id is required"
            }, status=400)

        if not user_input:
            return JsonResponse({
                "isSuccess": False,
                "data": None,
                "error": ERROR_MESSAGES["MISSING_MESSAGE"]
            }, status=400)

        # Normalize user message
        user_message = user_input if isinstance(user_input, str) else json.dumps(user_input)

        # STEP 1–2: Get or create conversation
        conversation, _ = Conversation.objects.get_or_create(
            session_id=session_id,
            defaults={"stage": "greeting", "channel": "website"}
        )

        # STEP 3: Save user message
        Message.objects.create(
            conversation=conversation,
            role="user",
            content=user_message
        )

        # STEP 4: Orchestrate conversation
        next_stage = orchestrate_conversation(
            user_message=user_message,
            current_stage=conversation.stage
        )

        prompt_type, file_name = get_prompt_for_stage(next_stage)

        # STEP 5: Call LLM
        start_time = time.time()

        result = generate_llm_response(
            data=user_message,
            prompt=prompt_type,
            file_name=file_name,
            engine=engine
        )

        bot_response = result.get("summary", "")

        # STEP 6: Save bot message
        Message.objects.create(
            conversation=conversation,
            role="bot",
            content=bot_response
        )

        # STEP 7: Lead extraction
        lead_data = extract_lead_from_message(user_message, engine)
        qualified = lead_data.is_qualified()

        # STEP 8: Save/update lead
        lead = None
        if lead_data.email:
            lead, _ = Lead.objects.get_or_create(
                email=lead_data.email,
                defaults={"source": "website"}
            )
        elif lead_data.phone:
            lead, _ = Lead.objects.get_or_create(
                phone=lead_data.phone,
                defaults={"source": "website"}
            )

        if lead:
            lead.name = lead_data.name or lead.name
            lead.company = lead_data.company or lead.company
            lead.problem = lead_data.problem or lead.problem
            lead.intent_level = lead_data.intent_level or lead.intent_level
            lead.qualified = qualified
            lead.save()

            conversation.lead = lead

        # STEP 9: Update conversation stage
        conversation.stage = next_stage
        conversation.save()

        duration = round(time.time() - start_time, 2)

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
                    "phone": lead_data.phone
                }
            },
            "error": None
        })

    except Exception:
        logger.exception("Unexpected error in chat_api")
        return JsonResponse({
            "isSuccess": False,
            "data": None,
            "error": ERROR_MESSAGES["LLM_INTERNAL_ERROR"]
        }, status=500)
