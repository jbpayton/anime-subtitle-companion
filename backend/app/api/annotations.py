import asyncio
import json
import logging
import time
from typing import Any

from fastapi import APIRouter, HTTPException

from ..db import get_db
from ..models.schemas import AnnotatedBlock, SubtitleBlock
from ..services.annotation_service import (
    annotate_batch, annotate_single, PROMPT_VERSION, BATCH_SIZE,
)
from ..config import settings

logger = logging.getLogger("app.api.annotations")

router = APIRouter()

# In-memory job tracking (single-server is fine for MVP)
_active_jobs: dict[str, dict[str, Any]] = {}


@router.post("/subtitles/{subtitle_set_id}/annotate")
async def trigger_annotation(subtitle_set_id: str, block_id: str | None = None):
    """Start annotation job. Returns immediately, runs in background."""
    # Don't allow duplicate jobs
    if subtitle_set_id in _active_jobs and _active_jobs[subtitle_set_id]["status"] == "running":
        job = _active_jobs[subtitle_set_id]
        return {
            "status": "already_running",
            "annotated": job["annotated"],
            "total": job["total"],
            "errors": job["errors"],
        }

    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, start_ms, end_ms, raw_text, display_text FROM subtitle_blocks WHERE subtitle_set_id = ? ORDER BY idx",
            (subtitle_set_id,),
        )
        rows = await cursor.fetchall()
        if not rows:
            raise HTTPException(404, "Subtitle set not found")

        all_blocks = [
            SubtitleBlock(
                id=row[0], start_ms=row[1], end_ms=row[2],
                raw_text=row[3], display_text=row[4],
                normalized_text=row[4].replace("\n", ""),
            )
            for row in rows
        ]

        if block_id:
            targets = [b for b in all_blocks if b.id == block_id]
            if not targets:
                raise HTTPException(404, "Block not found")
        else:
            cursor = await db.execute(
                "SELECT block_id FROM annotations WHERE block_id IN (SELECT id FROM subtitle_blocks WHERE subtitle_set_id = ?)",
                (subtitle_set_id,),
            )
            existing = {row[0] for row in await cursor.fetchall()}
            targets = [b for b in all_blocks if b.id not in existing]
    finally:
        await db.close()

    if not targets:
        return {"status": "complete", "annotated": 0, "total": len(all_blocks), "errors": 0}

    # Initialize job tracking
    job = {
        "status": "running",
        "total": len(targets),
        "annotated": 0,
        "errors": 0,
        "started_at": time.monotonic(),
        "current_batch": 0,
        "total_batches": (len(targets) + BATCH_SIZE - 1) // BATCH_SIZE,
    }
    _active_jobs[subtitle_set_id] = job

    # Fire and forget — run in background
    asyncio.create_task(_run_annotation_job(subtitle_set_id, targets, all_blocks, job))

    logger.info("=" * 60)
    logger.info(f"ANNOTATION JOB STARTED (background)")
    logger.info(f"  Subtitle set:   {subtitle_set_id}")
    logger.info(f"  To annotate:    {len(targets)} blocks in ~{job['total_batches']} batches of {BATCH_SIZE}")
    logger.info(f"  Model:          {settings.LLM_MODEL}")
    logger.info("=" * 60)

    return {
        "status": "started",
        "total": len(targets),
        "total_batches": job["total_batches"],
        "batch_size": BATCH_SIZE,
    }


async def _run_annotation_job(
    subtitle_set_id: str,
    targets: list[SubtitleBlock],
    all_blocks: list[SubtitleBlock],
    job: dict,
):
    """Background task that processes batches and saves results progressively."""
    job_start = time.monotonic()

    # Split into batches
    batches = [targets[i:i + BATCH_SIZE] for i in range(0, len(targets), BATCH_SIZE)]

    for batch_num, batch in enumerate(batches, 1):
        job["current_batch"] = batch_num
        batch_start = time.monotonic()

        logger.info(f"--- Batch {batch_num}/{len(batches)} ({len(batch)} blocks) ---")

        try:
            results, missed = await annotate_batch(batch, all_blocks)

            # Save results to DB immediately
            db = await get_db()
            try:
                for annotation in results:
                    await db.execute(
                        "INSERT OR REPLACE INTO annotations (block_id, annotation_json, model, prompt_version) VALUES (?, ?, ?, ?)",
                        (annotation.block_id, annotation.model_dump_json(), settings.LLM_MODEL, PROMPT_VERSION),
                    )
                await db.commit()
            finally:
                await db.close()

            job["annotated"] += len(results)

            # Retry missed blocks individually
            for block in missed:
                try:
                    annotation = await annotate_single(block, all_blocks)
                    db = await get_db()
                    try:
                        await db.execute(
                            "INSERT OR REPLACE INTO annotations (block_id, annotation_json, model, prompt_version) VALUES (?, ?, ?, ?)",
                            (annotation.block_id, annotation.model_dump_json(), settings.LLM_MODEL, PROMPT_VERSION),
                        )
                        await db.commit()
                    finally:
                        await db.close()
                    job["annotated"] += 1
                except Exception as e:
                    logger.error(f"Single-block retry failed for {block.id}: {e}")
                    job["errors"] += 1

            batch_elapsed = time.monotonic() - batch_start
            job_elapsed = time.monotonic() - job_start
            avg_per_batch = job_elapsed / batch_num
            remaining = avg_per_batch * (len(batches) - batch_num)

            logger.info(
                f"Batch {batch_num}/{len(batches)} done in {batch_elapsed:.1f}s | "
                f"Progress: {job['annotated']}/{job['total']} | "
                f"~{remaining:.0f}s remaining"
            )

        except Exception as e:
            logger.error(f"Batch {batch_num} FAILED: {e}")
            job["errors"] += len(batch)

        # Wait for the GPU to be ready before next batch
        if batch_num < len(batches):
            logger.info("Waiting for inference server to be ready for next batch...")
            try:
                from ..services.llm_client import _wait_for_server
                await _wait_for_server(f"{settings.LLM_API_BASE}/chat/completions", timeout=120)
                logger.info("inference server ready, proceeding to next batch")
            except Exception:
                logger.warning("Could not confirm server readiness, proceeding anyway")
                await asyncio.sleep(5)

    job_elapsed = time.monotonic() - job_start
    job["status"] = "complete"

    logger.info("=" * 60)
    logger.info(f"ANNOTATION JOB COMPLETE")
    logger.info(f"  Annotated:  {job['annotated']}/{job['total']}")
    logger.info(f"  Errors:     {job['errors']}")
    logger.info(f"  Total time: {job_elapsed:.1f}s")
    if job["annotated"] > 0:
        logger.info(f"  Avg/block:  {job_elapsed / job['annotated']:.1f}s")
    logger.info("=" * 60)


@router.get("/subtitles/{subtitle_set_id}/annotate/status")
async def annotation_status(subtitle_set_id: str):
    """Check progress of an annotation job."""
    job = _active_jobs.get(subtitle_set_id)

    # Also get actual count from DB
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM annotations WHERE block_id IN (SELECT id FROM subtitle_blocks WHERE subtitle_set_id = ?)",
            (subtitle_set_id,),
        )
        row = await cursor.fetchone()
        db_count = row[0] if row else 0

        cursor = await db.execute(
            "SELECT COUNT(*) FROM subtitle_blocks WHERE subtitle_set_id = ?",
            (subtitle_set_id,),
        )
        row = await cursor.fetchone()
        total_blocks = row[0] if row else 0
    finally:
        await db.close()

    return {
        "status": job["status"] if job else ("complete" if db_count == total_blocks else "idle"),
        "annotated": db_count,
        "total_blocks": total_blocks,
        "errors": job["errors"] if job else 0,
        "current_batch": job.get("current_batch", 0) if job else 0,
        "total_batches": job.get("total_batches", 0) if job else 0,
    }


@router.get("/subtitles/{subtitle_set_id}/annotations", response_model=list[AnnotatedBlock])
async def get_annotations(subtitle_set_id: str):
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT a.annotation_json FROM annotations a
               JOIN subtitle_blocks b ON a.block_id = b.id
               WHERE b.subtitle_set_id = ?
               ORDER BY b.idx""",
            (subtitle_set_id,),
        )
        rows = await cursor.fetchall()
        return [AnnotatedBlock(**json.loads(row[0])) for row in rows]
    finally:
        await db.close()
