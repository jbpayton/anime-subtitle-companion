from pydantic import BaseModel


class DictionaryLinks(BaseModel):
    jisho: str = ""
    wiktionary: str = ""


class Token(BaseModel):
    surface: str
    lemma: str
    reading: str
    part_of_speech: str
    gloss: str
    grammar_role: str
    conjugation: str | None = None
    dictionary_links: DictionaryLinks = DictionaryLinks()


class SubtitleBlock(BaseModel):
    id: str
    start_ms: int
    end_ms: int
    raw_text: str
    display_text: str
    normalized_text: str = ""


class AnnotatedBlock(BaseModel):
    block_id: str
    tokens: list[Token] = []
    grammar_notes: list[str] = []
    literal_translation: str = ""
    natural_translation: str = ""
    ambiguity_notes: list[str] = []
    confidence: float = 0.0


class SubtitleSetInfo(BaseModel):
    id: str
    filename: str
    title: str | None = None
    block_count: int = 0
    created_at: str = ""


class UploadResponse(BaseModel):
    subtitle_set_id: str
    filename: str
    block_count: int
