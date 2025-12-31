# Standard library imports
import os
import json
import time
import random
import logging
import hashlib
import textwrap
from typing import Callable

# Third-party imports
import requests
from openai import OpenAI, RateLimitError, APIStatusError, APIConnectionError
import ollama
from httpx import TimeoutException

# Django core imports
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import get_object_or_404


# App imports: utils
from utils.message import ERROR_MESSAGES, INFO_MESSAGES



logger = logging.getLogger(__name__)
CHUNK_SIZE = 10_000 


def count_tokens(text: str) -> int:
    """Estimate token count using a simple heuristic: 1 token ≈ 4 characters."""
    return max(len(text) // 4, 1)


def chunk_text(text: str, size: int = CHUNK_SIZE) -> list[str]:
    """
    Chunk line-based text (with line numbers) into blocks of approx 'size' characters
    without splitting mid-line.
    """
    lines = text.splitlines()
    chunks = []
    current_chunk = []
    current_length = 0

    for line in lines:
        line_length = len(line) + 1  
        if current_length + line_length > size:
            chunks.append('\n'.join(current_chunk))
            current_chunk = [line]
            current_length = line_length
        else:
            current_chunk.append(line)
            current_length += line_length

    if current_chunk:
        chunks.append('\n'.join(current_chunk))

    return chunks


def generate_dynamic_prompt(prompt_type: str, stakeholder_name: str) -> str:
    """
    Use Ollama LLM to dynamically generate a task-specific prompt based on the stakeholder and prompt type.
    """
    meta_prompt = textwrap.dedent(f"""
    You are a system that dynamically generates task instructions for an LLM-based code review or analysis assistant.

    Stakeholder: {stakeholder_name}
    Task Type: {prompt_type}

    Based on the stakeholder's role and the type of task, generate a clear, professional prompt that:
    - Instructs the assistant to perform the task in detail.
    - Uses the appropriate tone and language for the stakeholder.
    - Clearly communicates what kind of output is expected.
    - Avoids generic boilerplate; tailor it to the role and task type.

    Output Format: A single, concise paragraph. Do not add headers or extra explanations.
    """)

    logger.info(f"[Dynamic Prompt] Generating fallback prompt for stakeholder='{stakeholder_name}', type='{prompt_type}'")

    result, _ = generate_with_ollama(data="", prompt=meta_prompt)

    if not result.strip():
        logger.warning(f"[Dynamic Prompt] LLM returned empty fallback for '{prompt_type}' and '{stakeholder_name}'. Using generic fallback.")
        return f"As a {stakeholder_name.capitalize()}, please review the provided input and give feedback relevant to your role."

    return result.strip()


def load_prompt(prompt: str, stakeholder_name: str, file_name: str) -> str:
    """
    Load a stakeholder-specific prompt template from disk, or fall back to
    a file-based or dynamically generated prompt if not found.
    """

    base_dir = os.path.join(settings.PROMPTS_DIR, prompt.capitalize())

    # ---Try stakeholder-specific prompt ---
    stakeholder_prompt_path = os.path.join(base_dir, f"{stakeholder_name.lower()}.txt")
    # logger.info(INFO_MESSAGES["LOOKING_FOR_PROMPT"].format(path=stakeholder_prompt_path))

    if os.path.exists(stakeholder_prompt_path):
        with open(stakeholder_prompt_path, encoding="utf-8") as f:
            content = f.read()
        # logger.info(INFO_MESSAGES["PROMPT_LOADED"].format(length=len(content)))
        return content

    # ---Try fallback file prompt (e.g., 'generic', 'default', etc.) ---
    fallback_prompt_path = os.path.join(base_dir, f"{file_name.lower()}.txt")
    # logger.info(INFO_MESSAGES["LOOKING_FOR_PROMPT"].format(path=fallback_prompt_path))

    if os.path.exists(fallback_prompt_path):
        with open(fallback_prompt_path, encoding="utf-8") as f:
            content = f.read()
        # logger.info(INFO_MESSAGES["PROMPT_LOADED"].format(length=len(content)))
        return content

    # --- Final fallback: generate dynamically ---
    logger.warning(
        f"{ERROR_MESSAGES['PROMPT_NOT_FOUND']} Falling back to generated prompt. "
        f"Attempted paths: {stakeholder_prompt_path}, {fallback_prompt_path}"
    )

    # return generate_dynamic_prompt(prompt, stakeholder_name)
    return "You are a business lead generation assistant."


def generate_llm_response(
    data: str,
    prompt: str,    
    engine: str = 'ollama',
    stakeholder_name = None,
    file_name = None
) -> dict:
    """
    Main entrypoint to generate summary using the selected LLM engine.
    """    

    logger.info(f"[INPUT] Engine: {engine}, Stakeholder: {stakeholder_name}, Prompt: {prompt}, File Name: {file_name}")
    logger.info(f"[INPUT] Data snippet: {data[:200]}...")

    if not data.strip():
        raise ValueError(ERROR_MESSAGES["MISSING_DATA"])

    base_prompt = load_prompt(prompt, stakeholder_name if stakeholder_name else "", file_name if file_name else "")
    logger.info(f"[LOAD] Prompt snippet: {base_prompt[:200]}...")

    cache_key = f"llm_summary:{engine}:{stakeholder_name}:{hashlib.sha256((base_prompt + data).encode()).hexdigest()}"

    cached = cache.get(cache_key)
    if cached:
        logger.info("[CACHE HIT]")
        return cached

    engine_dispatch: dict[str, Callable] = {
        'ollama': lambda: generate_with_ollama(data, base_prompt),
        'openai': lambda: generate_with_openai(data, base_prompt, settings.LLM_MODEL_OPEN_AI),
        'lmstudio': lambda: generate_with_lmstudio(data, base_prompt, settings.LLM_MODEL_NAME)
    }

    if engine not in engine_dispatch:
        raise ValueError(f"{ERROR_MESSAGES['INVALID_ENGINE']} Got: {engine}")

    summary, duration = engine_dispatch[engine]()

    result = {
        "engine": engine,
        "duration": f"{duration}s",
        "summary": summary
    }

    cache.set(cache_key, result, timeout=3600)

    logger.info("[CACHE MISS] Cached result.")

    return result


def _get_ollama_client():
    """Initialize and return the Ollama client."""
    try:
        if settings.REMOTE_SERVER_IP_OLLAMA:
            logger.info(INFO_MESSAGES["OLLAMA_REMOTE_SERVER"].format(ip=settings.REMOTE_SERVER_IP_OLLAMA))
            return ollama.Client(host=settings.REMOTE_SERVER_IP_OLLAMA)
        else:
            logger.info(INFO_MESSAGES["OLLAMA_LOCAL_SERVER"])
            return ollama.Client()
    except Exception as e:
        logger.error(f"Failed to connect to Ollama server: {e}")
        raise RuntimeError(f"Cannot connect to Ollama server: {e}")


def generate_with_ollama(data: str, prompt: str) -> tuple[str, float]:
    """
    Generic chunked Ollama generator. Does not enforce specific output format.
    Used across all LLM workflows (not just code review).
    """
    logger.info(INFO_MESSAGES["OLLAMA_GENERATING"])
    model = settings.LLM_MODEL_NAME
    client = _get_ollama_client()

    chunks = chunk_text(data)
    start = time.time()
    full_response = []
    i = 0
    
    if not data:
        try: 
            logger.info(f"[Ollama] Generating from prompt only (len = {len(prompt)})")
            res = client.generate(model=model, prompt=prompt)
            result = res.get("response", "").strip()
        except TimeoutException as e:
            raise RuntimeError(f"Ollama timeout on chunk {i + 1}: {e}")
        except Exception as e:
            raise RuntimeError(f"Ollama failed on chunk {i + 1}: {e}")


    for i, chunk in enumerate(chunks):
        chunk_prompt = f"{prompt.strip()}\n\nData:\n{chunk.strip()}"

        try:
            logger.info(f"[Ollama] Chunk {i + 1}/{len(chunks)} (len={len(chunk)})")
            res = client.generate(model=model, prompt=chunk_prompt)
            result = res.get("response", "").strip()
            logger.info(f"[Ollama] Chunk {i + 1}/{len(chunks)} output generated (len={len(result)})")
            full_response.append(result)
        except TimeoutException as e:
            raise RuntimeError(f"Ollama timeout on chunk {i + 1}: {e}")
        except Exception as e:
            raise RuntimeError(f"Ollama failed on chunk {i + 1}: {e}")
    
    if len(full_response) > 1:
        
        final_prompt = (
            f"You were previously given a large input split into parts for the task:\n"
            f"{prompt.strip()}\n\n"
            f"The following are partial responses generated from each chunk of that data. "
            f"Please combine them into a single, complete, and coherent response that fulfills the original task. "
            f"Avoid repetition, ensure logical flow, and strictly follow the original format expected in the prompt.\n\n"
            f"**Instructions:**\n"
            f"- Preserve all meaningful points from the partial responses, even if they occur only once.\n"
            f"- Do not add any new headers, summaries, or commentary.\n"
            f"- Do not omit or rename any section headers or structural elements provided in the prompt.\n"
            f"- Ensure clarity, conciseness, and continuity across the final output.\n\n"
            f"Partial Responses:\n\n" + "\n\n".join(full_response)
        )

        logger.info(f"[Ollama] Combining all chunks into final prompt (length = {len(final_prompt)} characters)")


        response = client.generate(model=model, prompt=final_prompt)
        result = response.get("response", "")
    else:
        result = full_response[0] if full_response else ""

    duration = round(time.time() - start, 2)
    return result.strip(), duration


def generate_with_openai(data: str, prompt: str, model: str, fallback_model: str = "gpt-3.5-turbo") -> tuple[str, float]:
    """
    Generate summary using OpenAI's chat.completions API with robust retry, jitter, and optional model fallback.
    """
    logger.info("Generating summary using OpenAI...")

    api_key = getattr(settings, "OPENAI_API_KEY", None)
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in settings")

    client = OpenAI(api_key=api_key)
    logger.info("OpenAI API key loaded successfully.")

    start = time.time()
    max_retries = 5
    current_model = model

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=current_model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": data}
                ],
            )

            duration = round(time.time() - start, 2)
            logger.info(f"OpenAI generation completed in {duration}s with model {current_model}.")

            content = (
                response.choices[0].message.content
                if getattr(response, "choices", None)
                and len(response.choices) > 0
                and getattr(response.choices[0], "message", None)
                else ""
            )
            return content or "", duration

        except RateLimitError as e:
            wait_time = min(2 ** attempt + random.uniform(0.5, 1.5), 30)
            logger.warning(f"Rate limit hit on attempt {attempt + 1} with model {current_model}. Retrying in {wait_time:.1f}s...")
            time.sleep(wait_time)

        except APIStatusError as e:
            if e.status_code == 429:  # rate limit
                wait_time = min(2 ** attempt + random.uniform(0.5, 1.5), 30)
                logger.warning(f"HTTP {e.status_code} error on attempt {attempt + 1}. Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
                continue
            raise

        except APIConnectionError as e:
            wait_time = min(2 ** attempt + random.uniform(0.5, 1.5), 30)
            logger.warning(f"Connection error on attempt {attempt + 1}: {e}. Retrying in {wait_time:.1f}s...")
            time.sleep(wait_time)

        except Exception as e:
            logger.exception(f"Unexpected error during OpenAI generation: {e}")
            break


    # All retries failed
    duration = round(time.time() - start, 2)
    logger.error("OpenAI generation failed after multiple retries.")
    return "", duration



def generate_with_lmstudio(data: str, prompt: str, model: str) -> tuple[str, float]:
    """Generate summary using LM Studio API (local LLM server)."""
    logger.info(INFO_MESSAGES["LMSTUDIO_GENERATING"])
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": data}
        ],
        "temperature": 0.2
    }

    try:
        start = time.time()
        response = requests.post(
            f"{settings.LLM_LOCAL_API_BASE}/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        response.raise_for_status()
        result = response.json()
        duration = round(time.time() - start, 2)
        logger.info(INFO_MESSAGES["LMSTUDIO_COMPLETE"].format(duration=duration))
        return result['choices'][0]['message']['content'], duration
    except Exception as e:
        logger.error(ERROR_MESSAGES["LMSTUDIO_FAILURE"] + f" Detail: {str(e)}")
        raise RuntimeError(f"{ERROR_MESSAGES['LMSTUDIO_FAILURE']}: {str(e)}")


    # """Prepare data for final compilation"""
    # compilation_parts = [
    #     "=== PR REVIEW COMPILATION ===\n",
    #     f"Total files processed: {len(all_files)}\n",
    #     f"Total batches: {len(batch_summaries)}\n\n"
    # ]
    
    # for batch in batch_summaries:
    #     compilation_parts.append(
    #         f"BATCH {batch['batch_number']} ({batch['files_count']} files):\n"
    #         f"Files: {', '.join(batch['files_paths'])}\n"
    #         f"Summary: {batch['summary']}\n\n"
    #     )
    
    # compilation_parts.append(
    #     "\n=== INSTRUCTIONS ===\n"
    #     "Please provide a comprehensive PR review summary that:\n"
    #     "1. Identifies the main purpose and scope of changes\n"
    #     "2. Highlights key technical decisions\n"
    #     "3. Notes any potential concerns or improvements\n"
    #     "4. Summarizes the overall impact"
    # )
    
    # return "".join(compilation_parts)