import { useState, useEffect } from "react";
import type { Token, AnnotatedBlock, Flashcard } from "@/types/subtitle";
import { createFlashcard, listFlashcards, deleteFlashcard } from "@/lib/api";

type Tab = "word" | "sentence" | "flashcards";

interface Props {
  selectedToken: Token | null;
  selectedAnnotation: AnnotatedBlock | null;
  selectedBlockText: string;
  sourceFilename: string;
}

export function SidePanel({ selectedToken, selectedAnnotation, selectedBlockText, sourceFilename }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>("word");
  const [flashcards, setFlashcards] = useState<Flashcard[]>([]);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  // Auto-switch to word tab when a token is selected
  useEffect(() => {
    if (selectedToken) setActiveTab("word");
  }, [selectedToken]);

  // Load flashcards when switching to that tab
  useEffect(() => {
    if (activeTab === "flashcards") {
      listFlashcards().then(setFlashcards).catch(console.error);
    }
  }, [activeTab]);

  const handleSaveFlashcard = async () => {
    if (!selectedToken || !selectedAnnotation) return;
    try {
      await createFlashcard({
        surface: selectedToken.surface,
        lemma: selectedToken.lemma,
        reading: selectedToken.reading,
        part_of_speech: selectedToken.part_of_speech,
        gloss: selectedToken.gloss,
        grammar_role: selectedToken.grammar_role,
        conjugation: selectedToken.conjugation,
        sentence_jp: selectedBlockText,
        sentence_en: selectedAnnotation.natural_translation,
        source_file: sourceFilename,
        source_block_id: selectedAnnotation.block_id,
        notes: "",
      });
      setSaveStatus("Saved!");
      setTimeout(() => setSaveStatus(null), 2000);
      // Refresh if on flashcards tab
      if (activeTab === "flashcards") {
        const cards = await listFlashcards();
        setFlashcards(cards);
      }
    } catch (e) {
      setSaveStatus("Error saving");
      setTimeout(() => setSaveStatus(null), 2000);
    }
  };

  const handleDeleteFlashcard = async (id: number) => {
    try {
      await deleteFlashcard(id);
      setFlashcards((prev) => prev.filter((c) => c.id !== id));
    } catch (e) {
      console.error("Failed to delete:", e);
    }
  };

  return (
    <div className="w-96 bg-[#1a1a24] border-l border-[#2a2a3a] flex flex-col">
      {/* Tab bar */}
      <div className="flex border-b border-[#2a2a3a] shrink-0">
        {([["word", "Word"], ["sentence", "Sentence"], ["flashcards", "Cards"]] as const).map(
          ([key, label]) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`flex-1 px-3 py-2.5 text-xs font-medium transition-colors ${
                activeTab === key
                  ? "text-[#c4b5fd] border-b-2 border-[#6d28d9]"
                  : "text-[#71717a] hover:text-[#a1a1aa]"
              }`}
            >
              {label}
            </button>
          ),
        )}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === "word" && (
          <WordTab
            token={selectedToken}
            annotation={selectedAnnotation}
            onSave={handleSaveFlashcard}
            saveStatus={saveStatus}
          />
        )}
        {activeTab === "sentence" && (
          <SentenceTab
            annotation={selectedAnnotation}
            blockText={selectedBlockText}
          />
        )}
        {activeTab === "flashcards" && (
          <FlashcardsTab
            flashcards={flashcards}
            onDelete={handleDeleteFlashcard}
          />
        )}
      </div>
    </div>
  );
}

function WordTab({
  token,
  annotation,
  onSave,
  saveStatus,
}: {
  token: Token | null;
  annotation: AnnotatedBlock | null;
  onSave: () => void;
  saveStatus: string | null;
}) {
  if (!token) {
    return (
      <div className="flex items-center justify-center h-full text-[#52526a] text-center">
        <div>
          <p className="text-lg mb-1">単語</p>
          <p className="text-sm">Click a word to see details</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with save button */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-2xl font-bold text-[#c4b5fd]">{token.surface}</h3>
          {token.reading && token.reading !== token.surface && (
            <p className="text-sm text-[#a1a1aa]">{token.reading}</p>
          )}
        </div>
        <button
          onClick={onSave}
          disabled={!annotation}
          className="px-2 py-1 text-xs bg-[#2a2a3a] hover:bg-[#3a3a4a] disabled:opacity-30 rounded transition-colors"
          title="Save to flashcards"
        >
          {saveStatus ?? "+ Card"}
        </button>
      </div>

      {/* Core info */}
      <div className="space-y-3">
        <Field label="Dictionary Form" value={token.lemma} />
        <Field label="Part of Speech" value={token.part_of_speech} />
        <Field label="Meaning" value={token.gloss} />
        <Field label="Role in Sentence" value={token.grammar_role} />
        {token.conjugation && (
          <div>
            <p className="text-xs text-[#71717a] uppercase tracking-wider">Conjugation</p>
            <p className="text-sm text-[#a78bfa]">{token.conjugation}</p>
          </div>
        )}
      </div>

      {/* Dictionary links */}
      <div className="pt-3 border-t border-[#2a2a3a] space-y-2">
        <p className="text-xs text-[#71717a] uppercase tracking-wider">Look Up</p>
        <div className="flex gap-2">
          {token.dictionary_links.jisho && (
            <a
              href={token.dictionary_links.jisho}
              target="_blank"
              rel="noopener noreferrer"
              className="px-2 py-1 text-xs bg-[#2a2a3a] hover:bg-[#3a3a4a] text-[#818cf8] rounded transition-colors"
            >
              Jisho
            </a>
          )}
          {token.dictionary_links.wiktionary && (
            <a
              href={token.dictionary_links.wiktionary}
              target="_blank"
              rel="noopener noreferrer"
              className="px-2 py-1 text-xs bg-[#2a2a3a] hover:bg-[#3a3a4a] text-[#818cf8] rounded transition-colors"
            >
              Wiktionary
            </a>
          )}
        </div>
      </div>

      {/* Other tokens in the same block for quick switching */}
      {annotation && annotation.tokens.length > 1 && (
        <div className="pt-3 border-t border-[#2a2a3a]">
          <p className="text-xs text-[#71717a] uppercase tracking-wider mb-2">Other Words</p>
          <div className="flex flex-wrap gap-1">
            {annotation.tokens
              .filter((t) => t.surface !== token.surface)
              .map((t, i) => (
                <span
                  key={i}
                  className="text-xs px-1.5 py-0.5 bg-[#2a2a3a] text-[#a1a1aa] rounded"
                >
                  {t.surface}
                </span>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}

function SentenceTab({
  annotation,
  blockText,
}: {
  annotation: AnnotatedBlock | null;
  blockText: string;
}) {
  if (!annotation) {
    return (
      <div className="flex items-center justify-center h-full text-[#52526a] text-center">
        <div>
          <p className="text-lg mb-1">文法</p>
          <p className="text-sm">Select an annotated line to see grammar</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Original line */}
      <div>
        <p className="text-xs text-[#71717a] uppercase tracking-wider mb-1">Original</p>
        <p className="text-base">{blockText}</p>
      </div>

      {/* Translations */}
      {annotation.natural_translation && (
        <div>
          <p className="text-xs text-[#71717a] uppercase tracking-wider mb-1">Natural Translation</p>
          <p className="text-sm text-[#c4b5fd]">{annotation.natural_translation}</p>
        </div>
      )}
      {annotation.literal_translation && (
        <div>
          <p className="text-xs text-[#71717a] uppercase tracking-wider mb-1">Literal Translation</p>
          <p className="text-sm text-[#a1a1aa]">{annotation.literal_translation}</p>
        </div>
      )}

      {/* Grammar notes */}
      {annotation.grammar_notes.length > 0 && (
        <div>
          <p className="text-xs text-[#71717a] uppercase tracking-wider mb-2">Grammar Notes</p>
          <ul className="space-y-2">
            {annotation.grammar_notes.map((note, i) => (
              <li key={i} className="text-sm text-[#a1a1aa] pl-3 border-l-2 border-[#3a3a4a]">
                {note}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Ambiguity */}
      {annotation.ambiguity_notes.length > 0 && (
        <div>
          <p className="text-xs text-[#71717a] uppercase tracking-wider mb-2">Ambiguity / Nuance</p>
          <ul className="space-y-2">
            {annotation.ambiguity_notes.map((note, i) => (
              <li key={i} className="text-sm text-[#8b8ba0] pl-3 border-l-2 border-[#52526a]">
                {note}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Token breakdown table */}
      <div>
        <p className="text-xs text-[#71717a] uppercase tracking-wider mb-2">Word Breakdown</p>
        <div className="space-y-1">
          {annotation.tokens.map((t, i) => (
            <div key={i} className="flex items-baseline gap-2 text-xs">
              <span className="text-[#c4b5fd] font-medium min-w-[60px]">{t.surface}</span>
              <span className="text-[#71717a]">{t.reading !== t.surface ? t.reading : ""}</span>
              <span className="text-[#a1a1aa] flex-1">{t.gloss}</span>
              <span className="text-[#52526a]">{t.part_of_speech}</span>
            </div>
          ))}
        </div>
      </div>

      {annotation.confidence > 0 && (
        <p className="text-[10px] text-[#52526a]">
          Confidence: {Math.round(annotation.confidence * 100)}%
        </p>
      )}
    </div>
  );
}

function FlashcardsTab({
  flashcards,
  onDelete,
}: {
  flashcards: Flashcard[];
  onDelete: (id: number) => void;
}) {
  if (flashcards.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-[#52526a] text-center">
        <div>
          <p className="text-lg mb-1">Cards</p>
          <p className="text-sm">No flashcards yet. Click a word then "+ Card" to save one.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-[#71717a]">{flashcards.length} card{flashcards.length !== 1 ? "s" : ""}</p>
      {flashcards.map((card) => (
        <div key={card.id} className="p-3 bg-[#0f0f14] rounded-lg border border-[#2a2a3a] space-y-1">
          <div className="flex items-start justify-between">
            <div>
              <span className="text-base font-medium text-[#c4b5fd]">{card.surface}</span>
              {card.reading && card.reading !== card.surface && (
                <span className="text-xs text-[#71717a] ml-2">{card.reading}</span>
              )}
            </div>
            <button
              onClick={() => onDelete(card.id)}
              className="text-xs text-[#52526a] hover:text-red-400 transition-colors"
            >
              x
            </button>
          </div>
          <p className="text-sm text-[#a1a1aa]">{card.gloss}</p>
          {card.sentence_jp && (
            <p className="text-xs text-[#71717a] mt-1 pt-1 border-t border-[#2a2a3a]">
              {card.sentence_jp}
            </p>
          )}
          {card.sentence_en && (
            <p className="text-xs text-[#52526a] italic">{card.sentence_en}</p>
          )}
          <p className="text-[10px] text-[#3a3a4a]">{card.part_of_speech}</p>
        </div>
      ))}
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  if (!value) return null;
  return (
    <div>
      <p className="text-xs text-[#71717a] uppercase tracking-wider">{label}</p>
      <p className="text-sm">{value}</p>
    </div>
  );
}
