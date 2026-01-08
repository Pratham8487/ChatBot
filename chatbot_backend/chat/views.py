from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import BaseParser
from rest_framework.exceptions import ParseError
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.core.exceptions import ValidationError
from dataclasses import replace
import json
import re
import time
import logging

# from chatbot_backend.chat.services.langgraph_nodes.response_generator import generate_response_node
from utils.message import ERROR_MESSAGES
from chat.services.conversation_graph import build_conversation_graph
from chat.services.langgraph_state import ConversationState
from chat.services.conversation_graph import build_conversation_graph

# Build LangGraph once (important)
conversation_graph = build_conversation_graph()


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
        # -----------------------------
        # 1️⃣ Parse request
        # -----------------------------
        body = json.loads(request.body)
        session_id = body.get("session_id")
        user_input = body.get("data")

        if not session_id or not user_input:
            return JsonResponse({
                "isSuccess": False,
                "data": None,
                "error": "session_id and data are required"
            }, status=400)

        user_message = (
            user_input if isinstance(user_input, str)
            else json.dumps(user_input)
        )

        # -----------------------------
        # 2️⃣ DB READS + USER MESSAGE SAVE
        # -----------------------------
        with transaction.atomic():
            conversation, _ = Conversation.objects.get_or_create(
                session_id=session_id,
                defaults={
                    "stage": "greeting",
                    "channel": "website"
                }
            )

            Message.objects.create(
                conversation=conversation,
                role="user",
                content=user_message
            )

            existing_lead = conversation.lead

        # -----------------------------
        # 3️⃣ Build LangGraph State
        # -----------------------------
        state = ConversationState(
            session_id=session_id,
            user_message=user_message,
            stage=conversation.stage,
            lead_data={
                "email": existing_lead.email,
                "phone": existing_lead.phone,
                "company": existing_lead.company,
                "problem": existing_lead.problem,
            } if existing_lead else {},
            intent_level=existing_lead.intent_level if existing_lead else None,
            metadata={"engine": engine},
        )

        # -----------------------------
        # 4️⃣ LangGraph Invocation (NO DB LOCK)
        # -----------------------------
        start_time = time.time()

        result_dict = conversation_graph.invoke(state)

        # ✅ FIX: Use dataclasses.replace() to merge LangGraph results
        # dataclasses don't have .update() method - we need replace() to create
        # a new instance with updated values from all executed nodes
        result_state = replace(state, **result_dict)

        duration = round(time.time() - start_time, 2)

        bot_response = (
            result_state.bot_response
            or "Could you please tell me more about your requirements?"
        )

        # -----------------------------
        # 5️⃣ Persist BOT MESSAGE + STAGE
        # -----------------------------
        with transaction.atomic():
            Message.objects.create(
                conversation=conversation,
                role="bot",
                content=bot_response
            )

            conversation.stage = result_state.stage
            conversation.save()

        # -----------------------------
        # 6️⃣ Lead Persistence (SAFE)
        # -----------------------------
        lead = None
        lead_data = result_state.lead_data or {}

        email = lead_data.get("email")
        phone = lead_data.get("phone")

        if email or phone:
            with transaction.atomic():
                if email:
                    lead, _ = Lead.objects.get_or_create(
                        email=email,
                        defaults=lead_data
                    )
                elif phone:
                    lead, _ = Lead.objects.get_or_create(
                        phone=phone,
                        defaults=lead_data
                    )

                if lead:
                    lead.intent_level = result_state.intent_level
                    lead.qualified = result_state.qualified
                    lead.save()

                    conversation.lead = lead
                    conversation.save()

        # -----------------------------
        # 7️⃣ Final Response
        # -----------------------------
        return JsonResponse({
            "isSuccess": True,
            "data": {
                "engine": engine,
                "stage": result_state.stage,
                "duration": duration,
                "response": bot_response,
                "lead": {
                    "qualified": result_state.qualified,
                    "intent_level": result_state.intent_level,
                    "email": email,
                    "phone": phone,
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
