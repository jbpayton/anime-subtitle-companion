import asyncio
import logging
import time

import httpx

from ..config import settings

logger = logging.getLogger("app.llm")

MAX_RETRIES = 6
RETRY_BASE_DELAY = 10


async def _wait_for_server(url: str, timeout: float = 300.0) -> None:
    """Poll until inference server is accepting connections again."""
    start = time.monotonic()
    check_url = url.rsplit("/chat/completions", 1)[0] + "/models"

    while time.monotonic() - start < timeout:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(check_url)
                if resp.status_code == 200:
                    return
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout):
            pass
        waited = time.monotonic() - start
        logger.info(f"Waiting for inference server... ({waited:.0f}s)")
        await asyncio.sleep(5)

    raise httpx.ConnectError("inference server did not become available within timeout")


async def chat_completion(
    messages: list[dict],
    max_tokens: int | None = None,
    response_format: dict | None = None,
) -> dict:
    """Call the OpenAI-compatible chat completions endpoint with retry logic."""
    payload: dict = {
        "model": settings.LLM_MODEL,
        "messages": messages,
        "max_tokens": max_tokens or settings.LLM_MAX_TOKENS,
        "temperature": 0.3,
        # Let the model think — it produces far better structured output
        # Thinking goes into <think> tags which we strip during JSON extraction
        "chat_template_kwargs": {"enable_thinking": True},
    }
    if response_format:
        payload["response_format"] = response_format

    headers = {"Content-Type": "application/json"}
    if settings.LLM_API_KEY and settings.LLM_API_KEY != "not-needed":
        headers["Authorization"] = f"Bearer {settings.LLM_API_KEY}"

    url = f"{settings.LLM_API_BASE}/chat/completions"

    # Log the user message (truncated) for context
    user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    preview = user_msg[:120].replace("\n", " ")

    for attempt in range(MAX_RETRIES + 1):
        if attempt > 0:
            logger.info(f"LLM busy -- waiting for server to be ready (attempt {attempt + 1}/{MAX_RETRIES + 1})...")
            try:
                await _wait_for_server(url)
                logger.info("inference server is ready, sending request...")
            except httpx.ConnectError:
                logger.error("inference server did not become available, giving up")
                raise

        logger.info(f"LLM request  -> {preview}...")

        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=600.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                elapsed = time.monotonic() - start

                if resp.status_code != 200:
                    logger.error(f"LLM error {resp.status_code} after {elapsed:.1f}s: {resp.text[:500]}")
                    if attempt < MAX_RETRIES:
                        continue
                    resp.raise_for_status()

                result = resp.json()

                # Log response stats
                usage = result.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", "?")
                completion_tokens = usage.get("completion_tokens", "?")
                finish_reason = result.get("choices", [{}])[0].get("finish_reason", "?")
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                content_len = len(content)

                logger.info(
                    f"LLM response <- {elapsed:.1f}s | "
                    f"tokens: {prompt_tokens} in / {completion_tokens} out | "
                    f"finish: {finish_reason} | "
                    f"response: {content_len} chars"
                )

                if finish_reason == "length":
                    logger.warning("Response truncated (hit max_tokens) -- output may be incomplete")

                return result

        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            elapsed = time.monotonic() - start
            logger.warning(f"LLM connection failed after {elapsed:.1f}s: {type(e).__name__}")
            if attempt >= MAX_RETRIES:
                raise

        except httpx.ReadTimeout as e:
            elapsed = time.monotonic() - start
            logger.warning(f"LLM read timeout after {elapsed:.1f}s -- model may still be generating")
            if attempt >= MAX_RETRIES:
                raise

    raise RuntimeError("Unreachable")
