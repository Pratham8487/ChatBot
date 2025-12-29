import requests
import logging
import time
from typing import Callable
from django.conf import settings

# Configure logger
logger = logging.getLogger(__name__)

# Error messages
ERROR_MESSAGES = {
    "MISSING_DATA": "No data provided for AI processing",
    "INVALID_ENGINE": "Invalid engine specified",
}

OLLAMA_URL = settings.OLLAMA_URL


def generate_with_ollama(prompt: str) -> tuple[str, float]:
    """
    Generate response using Ollama engine.
    
    Args:
        prompt: The user message/prompt to send to Ollama
        
    Returns:
        Tuple of (response_text, duration_in_seconds)
    """
    start_time = time.time()
    
    payload = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    }
    
    logger.info(f"[OLLAMA] Sending request to {OLLAMA_URL}")
    
    response = requests.post(OLLAMA_URL, json=payload)
    response.raise_for_status()
    
    duration = round(time.time() - start_time, 2)
    response_text = response.json().get("response", "")
    
    logger.info(f"[OLLAMA] Response received in {duration}s")
    
    return response_text, duration


def get_ai_response(user_message: str, engine: str = 'ollama') -> str:
    """
    Main entrypoint to generate AI response using the selected LLM engine.
    
    Args:
        user_message: The user's input message
        engine: The LLM engine to use ('ollama', 'openai', 'lmstudio')
        
    Returns:
        The AI-generated response text
        
    Raises:
        ValueError: If data is missing or engine is invalid
    """
    logger.info(f"[INPUT] Engine: {engine}, Prompt: {user_message[:100]}...")
    
    if not user_message.strip():
        raise ValueError(ERROR_MESSAGES["MISSING_DATA"])
    
    # Engine dispatch dictionary
    engine_dispatch: dict[str, Callable] = {
        'ollama': lambda: generate_with_ollama(user_message),
        # Future engines can be added here:
        # 'openai': lambda: generate_with_openai(user_message),
        # 'lmstudio': lambda: generate_with_lmstudio(user_message)
    }
    
    if engine not in engine_dispatch:
        raise ValueError(f"{ERROR_MESSAGES['INVALID_ENGINE']} Got: {engine}")
    
    # Execute the selected engine
    summary, duration = engine_dispatch[engine]()
    
    result = {
        "summary": summary,
        "engine": engine,
        "duration": duration,
    }

    logger.info(
        f"[OUTPUT] Engine: {engine}, Duration: {duration}s, Response length: {len(summary)} chars"
    )

    return result

