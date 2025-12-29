from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import BaseParser
from rest_framework.exceptions import ParseError
from django.http import JsonResponse
import json
import re
import time
import logging

from .services.ai_service import get_ai_response

logger = logging.getLogger(__name__)

ERROR_MESSAGES = {
    "INVALID_JSON": "Invalid JSON body. Ensure special characters (quotes, newlines, backslashes) are properly escaped.",
    "LLM_INTERNAL_ERROR": "Internal LLM error",
    "MISSING_MESSAGE": "Message is required",
    "EMPTY_MESSAGE": "Message cannot be empty or whitespace only",
}


class RawJSONParser(BaseParser):
    """
    Custom parser that handles malformed JSON with unescaped special characters.
    This parser attempts to extract the message content even when JSON is invalid.
    """
    media_type = 'application/json'
    
    def parse(self, stream, media_type=None, parser_context=None):
        """
        Parse the incoming bytestream as JSON, with fallback for malformed JSON.
        """
        try:
            raw_data = stream.read().decode('utf-8')
        except UnicodeDecodeError as e:
            logger.error(f"Unicode decode error: {e}")
            raise ParseError("Invalid encoding. Please use UTF-8.")
        
        if not raw_data.strip():
            raise ParseError("Empty request body")
        
        # First, try standard JSON parsing
        try:
            return json.loads(raw_data)
        except json.JSONDecodeError:
            logger.warning("Standard JSON parsing failed, attempting to extract message from raw body")
            
        # Fallback: Try to extract message from malformed JSON
        extracted_message = self._extract_message_from_raw(raw_data)
        
        if extracted_message is not None:
            return {"message": extracted_message}
        
        # If all extraction methods fail, raise a helpful error
        raise ParseError(ERROR_MESSAGES["INVALID_JSON"])
    
    def _extract_message_from_raw(self, raw_data: str) -> str | None:
        """
        Attempt to extract message content from malformed JSON.
        Handles cases where code snippets with special characters are sent.
        """
        # Method 1: Try to find "message" key and extract everything after it
        patterns = [
            # Match: "message": "content..." or "message": 'content...'
            r'"message"\s*:\s*"(.*)',
            r'"message"\s*:\s*\'(.*)',
            r"'message'\s*:\s*\"(.*)",
            r"'message'\s*:\s*'(.*)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, raw_data, re.DOTALL)
            if match:
                content = match.group(1)
                # Remove trailing quote and brace if present
                content = self._clean_extracted_content(content)
                if content:
                    return content
        
        # Method 2: If the body looks like it's just raw text (not JSON at all)
        # treat the entire body as the message
        stripped = raw_data.strip()
        if not stripped.startswith('{') and not stripped.startswith('['):
            return stripped
        
        # Method 3: Try to fix common JSON issues and re-parse
        fixed_json = self._attempt_json_fix(raw_data)
        if fixed_json:
            try:
                parsed = json.loads(fixed_json)
                return parsed.get("message")
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _clean_extracted_content(self, content: str) -> str:
        """
        Clean extracted content by removing trailing JSON artifacts.
        """
        # Remove trailing patterns like: "} or "}  or '\n}
        content = re.sub(r'["\']?\s*\}\s*$', '', content, flags=re.DOTALL)
        # Remove trailing quote
        content = re.sub(r'["\']$', '', content)
        return content.strip()
    
    def _attempt_json_fix(self, raw_data: str) -> str | None:
        """
        Attempt to fix common JSON formatting issues.
        """
        try:
            # Find the message value boundaries
            match = re.search(r'"message"\s*:\s*"', raw_data)
            if not match:
                return None
            
            start_idx = match.end()
            
            # Find the end of the message value (last " before })
            # This is tricky because the content might have quotes
            end_match = re.search(r'"\s*\}\s*$', raw_data)
            if not end_match:
                return None
            
            end_idx = end_match.start()
            
            # Extract the raw message content
            raw_message = raw_data[start_idx:end_idx]
            
            # Properly escape the content for JSON
            escaped_message = self._escape_for_json(raw_message)
            
            return f'{{"message": "{escaped_message}"}}'
        except Exception as e:
            logger.debug(f"JSON fix attempt failed: {e}")
            return None
    
    def _escape_for_json(self, text: str) -> str:
        """
        Properly escape a string for JSON.
        """
        # Order matters: escape backslashes first
        text = text.replace('\\', '\\\\')
        text = text.replace('"', '\\"')
        text = text.replace('\n', '\\n')
        text = text.replace('\r', '\\r')
        text = text.replace('\t', '\\t')
        # Handle other control characters
        text = re.sub(r'[\x00-\x1f]', lambda m: f'\\u{ord(m.group(0)):04x}', text)
        return text


def sanitize_message(message: str) -> str:
    """
    Sanitize and clean the user message.
    Preserves the actual content but ensures it's safe to process.
    
    Args:
        message: The raw user message
        
    Returns:
        Cleaned message string
    """
    if not message:
        return ""
    
    # Convert to string if not already
    message = str(message)
    
    # Strip leading/trailing whitespace
    message = message.strip()
    
    # Remove null bytes (can cause issues)
    message = message.replace('\x00', '')
    
    # Normalize line endings to \n
    message = message.replace('\r\n', '\n').replace('\r', '\n')
    
    return message


def create_error_response(error_message: str, status_code: int = 400) -> JsonResponse:
    """
    Create a standardized error response.
    
    Args:
        error_message: The error message to include
        status_code: HTTP status code
        
    Returns:
        JsonResponse with error details
    """
    return JsonResponse({
        'isSuccess': False,
        'data': None,
        'error': error_message
    }, status=status_code)


def create_success_response(data: dict) -> JsonResponse:
    """
    Create a standardized success response.
    
    Args:
        data: The data to include in the response
        
    Returns:
        JsonResponse with success details
    """
    return JsonResponse({
        'isSuccess': True,
        'data': data,
        'error': None
    }, status=200)


@api_view(["POST"])
@parser_classes([RawJSONParser])
def chat_api(request):
    """
    Chat API endpoint that handles user messages and returns AI responses.
    
    This endpoint is robust against:
    - Malformed JSON with unescaped special characters
    - Code snippets with quotes, newlines, and backslashes
    - Empty or missing messages
    - Various encoding issues
    
    Expected request body:
        {"message": "Your message or code here"}
    
    Returns:
        JSON response with AI-generated response or error details
    """
    start_time = time.time()
    
    try:
        # Extract message from request data
        # The RawJSONParser handles malformed JSON, so request.data should be available
        try:
            user_message = request.data.get("message")
        except ParseError as e:
            logger.warning(f"Parse error while accessing request data: {e}")
            return create_error_response(str(e), 400)
        except Exception as e:
            logger.error(f"Unexpected error accessing request data: {e}")
            # Try to get raw body as fallback
            try:
                raw_body = request.body.decode('utf-8')
                user_message = raw_body if raw_body.strip() else None
            except Exception:
                return create_error_response(ERROR_MESSAGES["INVALID_JSON"], 400)
        
        # Validate message presence
        if user_message is None:
            logger.warning("No message provided in request")
            return create_error_response(ERROR_MESSAGES["MISSING_MESSAGE"], 400)
        
        # Sanitize the message
        user_message = sanitize_message(user_message)
        
        # Validate message is not empty after sanitization
        if not user_message:
            logger.warning("Empty message after sanitization")
            return create_error_response(ERROR_MESSAGES["EMPTY_MESSAGE"], 400)
        
        # Log the incoming request (truncate long messages)
        log_message = user_message[:200] + "..." if len(user_message) > 200 else user_message
        logger.info(f"Processing chat request. Message preview: {log_message}")
        
        # Get AI response
        result = get_ai_response(user_message)
        logger.info(f"Result of the get_ai_response: {result}")
        
        # Process the result
        if isinstance(result, dict):
            summary = result.get("summary", "")
            engine = result.get("engine", "unknown")
            duration = result.get("duration", round(time.time() - start_time, 2))
        else:
            summary = str(result) if result else ""
            engine = "Llama3"
            duration = round(time.time() - start_time, 2)
        
        # Validate we got a response
        if not summary:
            logger.error("Empty response from AI service")
            return create_error_response("AI service returned empty response", 500)
        
        return create_success_response({
            "engine": engine,
            "duration": duration,
            "response": summary,
        })

    except ParseError as e:
        logger.error(f"JSON parse error: {e}")
        return create_error_response(str(e), 400)

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return create_error_response(
            f"{ERROR_MESSAGES['INVALID_JSON']} Details: {str(e)}", 
            400
        )

    except ValueError as e:
        logger.error(f"Value error: {e}")
        return create_error_response(str(e), 400)

    except ConnectionError as e:
        logger.error(f"Connection error to AI service: {e}")
        return create_error_response(
            "Failed to connect to AI service. Please try again later.", 
            503
        )

    except TimeoutError as e:
        logger.error(f"Timeout error: {e}")
        return create_error_response(
            "Request timed out. Please try again with a shorter message.", 
            504
        )

    except Exception as e:
        logger.exception("An unexpected error occurred during chat processing")
        return create_error_response(
            f"{ERROR_MESSAGES['LLM_INTERNAL_ERROR']}: {str(e)}", 
            500
        )
