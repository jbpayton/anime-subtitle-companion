import json
import logging
import re
import time

from ..models.schemas import AnnotatedBlock, SubtitleBlock, Token
from .dictionary_links import generate_links
from .llm_client import chat_completion

logger = logging.getLogger("app.annotation")

PROMPT_VERSION = "v2-batch"

BATCH_SIZE = 10  # blocks per LLM call


def _extract_json(text: str) -> dict | list | None:
    """Extract JSON from LLM output, handling think tags and markdown fences."""
    # Strip <think>...</think> blocks (Qwen think tags)
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    cleaned = cleaned.strip()

    # Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code fences
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try finding a JSON array or object
    for pattern in [r"\[.*\]", r"\{.*\}"]:
        match = re.search(pattern, cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

    return None


BATCH_SYSTEM_PROMPT = """You are a Japanese language analysis engine for anime subtitle learning tools. You will receive multiple numbered subtitle lines. For EACH line, produce a rich structured analysis for Japanese learners.

Think carefully about each line — use the surrounding context to resolve ambiguity, infer omitted subjects, and choose accurate translations. Take your time reasoning, then output the result.

Your final output must be a JSON array where each element matches this schema:
{
  "line_number": 1,
  "tokens": [
    {
      "surface": "the exact text as it appears",
      "lemma": "dictionary form",
      "reading": "hiragana reading",
      "part_of_speech": "noun/verb/adjective/particle/etc",
      "gloss": "English meaning in this context",
      "grammar_role": "role in this sentence",
      "conjugation": "conjugation form if applicable, null otherwise"
    }
  ],
  "grammar_notes": ["explanation of grammar points for learners"],
  "literal_translation": "word-by-word English",
  "natural_translation": "natural English translation",
  "ambiguity_notes": ["any alternate interpretations"],
  "confidence": 0.0 to 1.0
}

Guidelines:
- Analyze EVERY numbered line — do not skip any
- Tokenize accurately — every character must be covered by exactly one token
- Group verb phrases naturally (e.g. 聴いてしまった as one token, not split into particles)
- Note conjugation forms and contractions (e.g. ていた -> てた)
- Recognize slang, internet language, and subculture terms (勢, コミケ, etc.)
- Keep glosses concise and context-appropriate
- Be honest about ambiguity rather than guessing confidently
- Grammar notes should be pedagogically useful — explain WHY, not just WHAT

After thinking, output ONLY the JSON array."""


def _build_batch_messages(
    batch: list[SubtitleBlock], all_blocks: list[SubtitleBlock]
) -> list[dict]:
    """Build messages for a batch of blocks, including surrounding context."""
    # Find context before first block and after last block
    first_start = batch[0].start_ms
    last_start = batch[-1].start_ms

    context_before = [b for b in all_blocks if b.start_ms < first_start][-3:]
    context_after = [b for b in all_blocks if b.start_ms > last_start][:3]

    lines = []
    if context_before:
        lines.append("Context (preceding lines, do NOT analyze these):")
        for b in context_before:
            lines.append(f"  {b.display_text}")
        lines.append("")

    lines.append("Lines to analyze:")
    for i, block in enumerate(batch, 1):
        lines.append(f"  [{i}] {block.display_text}")

    if context_after:
        lines.append("")
        lines.append("Context (following lines, do NOT analyze these):")
        for b in context_after:
            lines.append(f"  {b.display_text}")

    return [
        {"role": "system", "content": BATCH_SYSTEM_PROMPT},
        {"role": "user", "content": "\n".join(lines)},
    ]


def _parse_annotation(data: dict, block: SubtitleBlock) -> AnnotatedBlock:
    """Convert a raw LLM annotation dict into an AnnotatedBlock."""
    tokens = []
    for t in data.get("tokens", []):
        token = Token(
            surface=t.get("surface", ""),
            lemma=t.get("lemma", ""),
            reading=t.get("reading", ""),
            part_of_speech=t.get("part_of_speech", ""),
            gloss=t.get("gloss", ""),
            grammar_role=t.get("grammar_role", ""),
            conjugation=t.get("conjugation"),
            dictionary_links=generate_links(
                t.get("surface", ""), t.get("lemma", "")
            ),
        )
        tokens.append(token)

    return AnnotatedBlock(
        block_id=block.id,
        tokens=tokens,
        grammar_notes=data.get("grammar_notes", []),
        literal_translation=data.get("literal_translation", ""),
        natural_translation=data.get("natural_translation", ""),
        ambiguity_notes=data.get("ambiguity_notes", []),
        confidence=data.get("confidence", 0.0),
    )


async def annotate_batch(
    batch: list[SubtitleBlock], all_blocks: list[SubtitleBlock]
) -> list[AnnotatedBlock]:
    """Annotate a batch of subtitle blocks in a single LLM call."""
    batch_ids = [b.id for b in batch]
    batch_preview = " | ".join(b.display_text[:30] for b in batch[:3])
    logger.info(f"Batch of {len(batch)} blocks: {batch_preview}...")

    messages = _build_batch_messages(batch, all_blocks)

    start = time.monotonic()
    response = await chat_completion(messages=messages, response_format=None)
    llm_time = time.monotonic() - start

    content = response["choices"][0]["message"]["content"]
    parsed = _extract_json(content)

    # Handle retry if JSON extraction fails
    if parsed is None:
        logger.warning(f"Batch: invalid JSON ({len(content)} chars), retrying...")
        logger.debug(f"Raw output: {content[:500]}")
        messages.append({"role": "assistant", "content": content})
        messages.append({
            "role": "user",
            "content": "That was not valid JSON. Respond with ONLY a JSON array of annotation objects. No markdown, no explanation.",
        })
        response = await chat_completion(messages=messages, response_format=None)
        content = response["choices"][0]["message"]["content"]
        parsed = _extract_json(content)
        if parsed is None:
            logger.error(f"Batch: JSON extraction failed after retry. Raw: {content[:300]}")
            raise ValueError("LLM failed to produce valid JSON after retry")

    # Normalize: if we got a single object, wrap in list
    if isinstance(parsed, dict):
        parsed = [parsed]

    if not isinstance(parsed, list):
        raise ValueError(f"Expected JSON array, got {type(parsed).__name__}")

    # Map results back to blocks by line_number (1-indexed)
    results = []
    for item in parsed:
        line_num = item.get("line_number")
        if line_num is not None and 1 <= line_num <= len(batch):
            block = batch[line_num - 1]
            try:
                annotation = _parse_annotation(item, block)
                results.append(annotation)
                logger.info(
                    f"  [{line_num}/{len(batch)}] {block.id} OK | "
                    f"{len(annotation.tokens)} tokens | "
                    f"\"{annotation.natural_translation[:50]}\""
                )
            except Exception as e:
                logger.error(f"  [{line_num}/{len(batch)}] parse error: {e}")

    # Check for any blocks that didn't get annotated
    annotated_ids = {r.block_id for r in results}
    missed = [b for b in batch if b.id not in annotated_ids]
    if missed:
        logger.warning(f"Batch: {len(missed)} blocks not in LLM response, will retry individually")

    logger.info(
        f"Batch complete: {len(results)}/{len(batch)} annotated in {llm_time:.1f}s "
        f"({llm_time / max(len(results), 1):.1f}s/block effective)"
    )

    return results, missed


# Keep single-block annotator as fallback for missed blocks
async def annotate_single(
    block: SubtitleBlock, all_blocks: list[SubtitleBlock]
) -> AnnotatedBlock:
    """Fallback: annotate a single block."""
    logger.info(f"Single-block fallback: {block.id} \"{block.display_text[:40]}\"")

    context_before = [b for b in all_blocks if b.start_ms < block.start_ms][-3:]
    context_after = [b for b in all_blocks if b.start_ms > block.start_ms][:3]

    lines = []
    if context_before:
        lines.append("Context (preceding):")
        for b in context_before:
            lines.append(f"  {b.display_text}")
        lines.append("")
    lines.append(f"Line to analyze:")
    lines.append(f"  [1] {block.display_text}")
    if context_after:
        lines.append("")
        lines.append("Context (following):")
        for b in context_after:
            lines.append(f"  {b.display_text}")

    messages = [
        {"role": "system", "content": BATCH_SYSTEM_PROMPT},
        {"role": "user", "content": "\n".join(lines)},
    ]

    response = await chat_completion(messages=messages, response_format=None)
    content = response["choices"][0]["message"]["content"]
    parsed = _extract_json(content)

    if parsed is None:
        raise ValueError("LLM failed to produce valid JSON for single block")

    if isinstance(parsed, list) and len(parsed) > 0:
        parsed = parsed[0]
    if not isinstance(parsed, dict):
        raise ValueError(f"Expected dict, got {type(parsed).__name__}")

    return _parse_annotation(parsed, block)
