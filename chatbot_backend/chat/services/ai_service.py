import requests
import logging
import time
from typing import Callable
from django.conf import settings

# Configure logger
logger = logging.getLogger(__name__)

# utils message Import
from utils.message import ERROR_MESSAGES


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
