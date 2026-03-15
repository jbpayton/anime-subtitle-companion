import logging
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException

from ..db import get_db

logger = logging.getLogger("app.api.flashcards")

router = APIRouter()


class FlashcardCreate(BaseModel):
    surface: str
    lemma: str
    reading: str = ""
    part_of_speech: str = ""
    gloss: str
    grammar_role: str = ""
    conjugation: str | None = None
    sentence_jp: str = ""
    sentence_en: str = ""
    source_file: str = ""
    source_block_id: str = ""
    notes: str = ""


class Flashcard(FlashcardCreate):
    id: int
    created_at: str


@router.post("/flashcards", response_model=Flashcard)
async def create_flashcard(card: FlashcardCreate):
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO flashcards
               (surface, lemma, reading, part_of_speech, gloss, grammar_role,
                conjugation, sentence_jp, sentence_en, source_file, source_block_id, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                card.surface, card.lemma, card.reading, card.part_of_speech,
                card.gloss, card.grammar_role, card.conjugation,
                card.sentence_jp, card.sentence_en, card.source_file,
                card.source_block_id, card.notes,
            ),
        )
        await db.commit()
        card_id = cursor.lastrowid

        cursor = await db.execute("SELECT * FROM flashcards WHERE id = ?", (card_id,))
        row = await cursor.fetchone()
        logger.info(f"Flashcard created: {card.surface} ({card.gloss})")
        return Flashcard(
            id=row[0], surface=row[1], lemma=row[2], reading=row[3],
            part_of_speech=row[4], gloss=row[5], grammar_role=row[6],
            conjugation=row[7], sentence_jp=row[8], sentence_en=row[9],
            source_file=row[10], source_block_id=row[11], notes=row[12],
            created_at=row[13],
        )
    finally:
        await db.close()


@router.get("/flashcards", response_model=list[Flashcard])
async def list_flashcards():
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM flashcards ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        return [
            Flashcard(
                id=row[0], surface=row[1], lemma=row[2], reading=row[3],
                part_of_speech=row[4], gloss=row[5], grammar_role=row[6],
                conjugation=row[7], sentence_jp=row[8], sentence_en=row[9],
                source_file=row[10], source_block_id=row[11], notes=row[12],
                created_at=row[13],
            )
            for row in rows
        ]
    finally:
        await db.close()


@router.delete("/flashcards/{card_id}")
async def delete_flashcard(card_id: int):
    db = await get_db()
    try:
        cursor = await db.execute("DELETE FROM flashcards WHERE id = ?", (card_id,))
        await db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(404, "Flashcard not found")
        logger.info(f"Flashcard {card_id} deleted")
        return {"deleted": True}
    finally:
        await db.close()


@router.patch("/flashcards/{card_id}")
async def update_flashcard_notes(card_id: int, notes: str):
    db = await get_db()
    try:
        cursor = await db.execute(
            "UPDATE flashcards SET notes = ? WHERE id = ?", (notes, card_id)
        )
        await db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(404, "Flashcard not found")
        return {"updated": True}
    finally:
        await db.close()
