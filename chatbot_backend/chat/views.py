from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import BaseParser
from rest_framework.exceptions import ParseError
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.core.exceptions import ValidationError
import json
import re
import time
import logging

from chatbot_backend.chat.services.langgraph_nodes.response_generator import generate_response_node
from utils.message import ERROR_MESSAGES
from chat.services.conversation_graph import build_conversation_graph
from chat.services.langgraph_state import ConversationState


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
@transaction.atomic
def chat_api(request):
    engine = request.GET.get("engine", "ollama").lower()
    logger.info(f"Engine selected: {engine}")

    try:
        body = json.loads(request.body)
        session_id = body.get("session_id")
        user_input = body.get("data")

        if not session_id or not user_input:
            return JsonResponse({
                "isSuccess": False,
                "data": None,
                "error": "session_id and data are required"
            }, status=400)

        user_message = user_input if isinstance(user_input, str) else json.dumps(user_input)

        # 1️⃣ Get or create conversation
        conversation, _ = Conversation.objects.get_or_create(
            session_id=session_id,
            defaults={"stage": "greeting", "channel": "website"}
        )

        # 2️⃣ Save user message
        Message.objects.create(
            conversation=conversation,
            role="user",
            content=user_message
        )

        # 3️⃣ Build LangGraph state
        state = ConversationState(
            user_message=user_message,
            stage=conversation.stage,
            metadata={"engine": engine}
        )

        start_time = time.time()

        # 4️⃣ Run LangGraph (THIS IS THE BRAIN)
        result_state = conversation_graph.invoke(state)

        duration = round(time.time() - start_time, 2)

        # 5️⃣ Save bot response
        Message.objects.create(
            conversation=conversation,
            role="bot",
            content=result_state.bot_response
        )

        # 6️⃣ Persist stage update
        conversation.stage = result_state.stage
        conversation.save()

        # 7️⃣ Persist lead if available
        lead = None
        if result_state.lead_data:
            email = result_state.lead_data.get("email")
            phone = result_state.lead_data.get("phone")

            if email or phone:
                lead, _ = Lead.objects.get_or_create(
                    email=email,
                    defaults=result_state.lead_data
                )
                lead.intent_level = result_state.intent_level
                lead.qualified = result_state.qualified
                lead.save()

                conversation.lead = lead
                conversation.save()

        return JsonResponse({
            "isSuccess": True,
            "data": {
                "engine": engine,
                "stage": result_state.stage,
                "duration": duration,
                "response": result_state.bot_response,
                "lead": {
                    "qualified": result_state.qualified,
                    "intent_level": result_state.intent_level,
                    "email": result_state.lead_data.get("email") if result_state.lead_data else None,
                    "phone": result_state.lead_data.get("phone") if result_state.lead_data else None,
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
