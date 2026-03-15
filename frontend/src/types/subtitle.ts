export interface DictionaryLinks {
  jisho: string;
  wiktionary: string;
}

export interface Token {
  surface: string;
  lemma: string;
  reading: string;
  part_of_speech: string;
  gloss: string;
  grammar_role: string;
  conjugation: string | null;
  dictionary_links: DictionaryLinks;
}

export interface SubtitleBlock {
  id: string;
  start_ms: number;
  end_ms: number;
  raw_text: string;
  display_text: string;
  normalized_text: string;
}

export interface AnnotatedBlock {
  block_id: string;
  tokens: Token[];
  grammar_notes: string[];
  literal_translation: string;
  natural_translation: string;
  ambiguity_notes: string[];
  confidence: number;
}

export interface SubtitleSetInfo {
  id: string;
  filename: string;
  title: string | null;
  block_count: number;
  created_at: string;
}

export interface Flashcard {
  id: number;
  surface: string;
  lemma: string;
  reading: string;
  part_of_speech: string;
  gloss: string;
  grammar_role: string;
  conjugation: string | null;
  sentence_jp: string;
  sentence_en: string;
  source_file: string;
  source_block_id: string;
  notes: string;
  created_at: string;
}
