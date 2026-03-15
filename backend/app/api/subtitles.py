import logging
import uuid

from fastapi import APIRouter, UploadFile, File, HTTPException

from ..db import get_db
from ..models.schemas import SubtitleBlock, SubtitleSetInfo, UploadResponse
from ..services.subtitle_parser import parse_subtitle_file

logger = logging.getLogger("app.api.subtitles")

router = APIRouter()


@router.post("/subtitles/upload", response_model=UploadResponse)
async def upload_subtitle(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "No filename provided")

    logger.info(f"Upload received: {file.filename} ({file.size or '?'} bytes)")

    content = await file.read()
    subtitle_set_id = uuid.uuid4().hex[:12]

    try:
        blocks = parse_subtitle_file(content, file.filename, subtitle_set_id)
    except Exception as e:
        logger.error(f"Parse failed for {file.filename}: {e}")
        raise HTTPException(400, f"Failed to parse subtitle file: {e}")

    logger.info(f"Parsed {len(blocks)} blocks from {file.filename}")

    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO subtitle_sets (id, filename) VALUES (?, ?)",
            (subtitle_set_id, file.filename),
        )
        for i, block in enumerate(blocks):
            await db.execute(
                "INSERT INTO subtitle_blocks (id, subtitle_set_id, idx, start_ms, end_ms, raw_text, display_text) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (block.id, subtitle_set_id, i, block.start_ms, block.end_ms, block.raw_text, block.display_text),
            )
        await db.commit()
        logger.info(f"Stored subtitle set {subtitle_set_id} ({len(blocks)} blocks)")
    finally:
        await db.close()

    return UploadResponse(
        subtitle_set_id=subtitle_set_id,
        filename=file.filename,
        block_count=len(blocks),
    )


@router.get("/subtitles", response_model=list[SubtitleSetInfo])
async def list_subtitle_sets():
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT s.id, s.filename, s.title, s.created_at,
                      COUNT(b.id) as block_count
               FROM subtitle_sets s
               LEFT JOIN subtitle_blocks b ON b.subtitle_set_id = s.id
               GROUP BY s.id
               ORDER BY s.created_at DESC"""
        )
        rows = await cursor.fetchall()
        logger.info(f"Listing {len(rows)} subtitle sets")
        return [
            SubtitleSetInfo(
                id=row[0],
                filename=row[1],
                title=row[2],
                created_at=row[3],
                block_count=row[4],
            )
            for row in rows
        ]
    finally:
        await db.close()


@router.get("/subtitles/{subtitle_set_id}/blocks", response_model=list[SubtitleBlock])
async def get_blocks(subtitle_set_id: str):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, start_ms, end_ms, raw_text, display_text FROM subtitle_blocks WHERE subtitle_set_id = ? ORDER BY idx",
            (subtitle_set_id,),
        )
        rows = await cursor.fetchall()
        if not rows:
            raise HTTPException(404, "Subtitle set not found")
        logger.info(f"Returning {len(rows)} blocks for set {subtitle_set_id}")
        return [
            SubtitleBlock(
                id=row[0],
                start_ms=row[1],
                end_ms=row[2],
                raw_text=row[3],
                display_text=row[4],
                normalized_text=row[4].replace("\n", ""),
            )
            for row in rows
        ]
    finally:
        await db.close()
