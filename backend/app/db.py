import aiosqlite

from .config import settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS subtitle_sets (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    title TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS subtitle_blocks (
    id TEXT PRIMARY KEY,
    subtitle_set_id TEXT NOT NULL REFERENCES subtitle_sets(id),
    idx INTEGER NOT NULL,
    start_ms INTEGER NOT NULL,
    end_ms INTEGER NOT NULL,
    raw_text TEXT NOT NULL,
    display_text TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS annotations (
    block_id TEXT PRIMARY KEY REFERENCES subtitle_blocks(id),
    annotation_json TEXT NOT NULL,
    model TEXT,
    prompt_version TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS flashcards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    surface TEXT NOT NULL,
    lemma TEXT NOT NULL,
    reading TEXT,
    part_of_speech TEXT,
    gloss TEXT NOT NULL,
    grammar_role TEXT,
    conjugation TEXT,
    sentence_jp TEXT,
    sentence_en TEXT,
    source_file TEXT,
    source_block_id TEXT,
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


async def init_db() -> None:
    async with aiosqlite.connect(settings.DATABASE_PATH) as db:
        await db.executescript(_SCHEMA)
        await db.commit()


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(settings.DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    return db
