from rest_framework.decorators import api_view
from django.http import JsonResponse
import json
import time
import logging

from .services.ai_service import get_ai_response

logger = logging.getLogger(__name__)

ERROR_MESSAGES = {
    "INVALID_JSON": "Invalid JSON body",
    "LLM_INTERNAL_ERROR": "Internal LLM error"
}


@api_view(["POST"])
def chat_api(request):
    try:
        user_message = request.data.get("message")

        if not user_message:
            return JsonResponse(
                {"isSuccess": False, "data": None, "error": "Message is required"},
                status=400
            )

        start = time.time()
        result = get_ai_response(user_message)
        logger.info(f"Result of the get_ai_response: {result}")
        # duration = time.time() - start

        if isinstance(result, dict):
            summary = result.get("summary")
            engine = result.get("engine")
            duration = result.get("duration")
        else:
            summary = str(result)
            engine = "Llama3"
            duration = round(time.time() - start,2)            

        return JsonResponse({
            "isSuccess": True,
            "data": {
                "engine": engine,
                "duration": duration,
                "response": summary,
            },
            "error": None
        }, status=200)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON body")
        return JsonResponse({
            'isSuccess': False,
            'data': None,
            'error': ERROR_MESSAGES["INVALID_JSON"]
        }, status=400)

    except Exception:
        logger.exception("An unexpected error occurred during summary generation")
        return JsonResponse({
            'isSuccess': False,
            'data': None,
            'error': ERROR_MESSAGES["LLM_INTERNAL_ERROR"]
        }, status=500)
