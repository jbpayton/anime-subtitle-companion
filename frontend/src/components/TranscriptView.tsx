import { useEffect, useRef, useState } from "react";
import type { SubtitleBlock, AnnotatedBlock, Token } from "@/types/subtitle";
import { SubtitleLine } from "./SubtitleLine";

function formatTimestamp(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

interface Props {
  blocks: SubtitleBlock[];
  annotations: Map<string, AnnotatedBlock>;
  activeBlockIndex: number;
  selectedBlockId: string | null;
  selectedTokenSurface?: string;
  onBlockClick: (index: number) => void;
  onTokenSelect: (token: Token, blockId: string) => void;
}

export function TranscriptView({
  blocks,
  annotations,
  activeBlockIndex,
  selectedBlockId,
  selectedTokenSurface,
  onBlockClick,
  onTokenSelect,
}: Props) {
  const activeRef = useRef<HTMLDivElement>(null);
  const [expandedBlocks, setExpandedBlocks] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (activeRef.current) {
      activeRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [activeBlockIndex]);

  const toggleExpand = (blockId: string) => {
    setExpandedBlocks((prev) => {
      const next = new Set(prev);
      if (next.has(blockId)) next.delete(blockId);
      else next.add(blockId);
      return next;
    });
  };

  if (blocks.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-[#71717a]">
        <div className="text-center">
          <p className="text-2xl mb-2">字幕</p>
          <p>Load a subtitle file to get started</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-2">
      {blocks.map((block, index) => {
        const isActive = index === activeBlockIndex;
        const isSelected = block.id === selectedBlockId;
        const annotation = annotations.get(block.id);
        const isExpanded = expandedBlocks.has(block.id);

        return (
          <div
            key={block.id}
            ref={isActive ? activeRef : null}
            className={`group rounded-lg transition-all ${
              isActive
                ? "bg-[#6d28d9]/15 border border-[#6d28d9]/40"
                : isSelected
                  ? "bg-[#2a2a3a]/60 border border-[#3a3a4a]"
                  : "hover:bg-[#1a1a24] border border-transparent"
            }`}
          >
            {/* Main clickable row */}
            <div
              onClick={() => onBlockClick(index)}
              className="p-3 cursor-pointer"
            >
              <div className="flex items-start gap-3">
                <span className="text-xs text-[#52526a] font-mono mt-1.5 shrink-0">
                  {formatTimestamp(block.start_ms)}
                </span>
                <div className="flex-1 min-w-0">
                  <SubtitleLine
                    text={block.display_text}
                    annotation={annotation}
                    onTokenSelect={(token) => onTokenSelect(token, block.id)}
                    selectedTokenSurface={isSelected ? selectedTokenSurface : undefined}
                  />

                  {/* Translation line */}
                  {annotation && annotation.natural_translation && (
                    <p className="text-sm text-[#8b8ba0] mt-2 italic">
                      {annotation.natural_translation}
                    </p>
                  )}
                </div>

                {/* Expand toggle for grammar notes */}
                {annotation && annotation.grammar_notes.length > 0 && (
                  <button
                    onClick={(e) => { e.stopPropagation(); toggleExpand(block.id); }}
                    className="text-xs text-[#52526a] hover:text-[#a1a1aa] mt-1 shrink-0 transition-colors"
                    title="Toggle grammar notes"
                  >
                    {isExpanded ? "[-]" : "[+]"}
                  </button>
                )}
              </div>
            </div>

            {/* Expanded grammar notes */}
            {isExpanded && annotation && (
              <div className="px-3 pb-3 ml-12 border-t border-[#2a2a3a]/50 pt-2 space-y-2">
                {annotation.grammar_notes.length > 0 && (
                  <div>
                    <p className="text-[10px] uppercase tracking-wider text-[#52526a] mb-1">Grammar</p>
                    <ul className="text-xs text-[#a1a1aa] space-y-0.5">
                      {annotation.grammar_notes.map((note, i) => (
                        <li key={i}>- {note}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {annotation.literal_translation && (
                  <div>
                    <p className="text-[10px] uppercase tracking-wider text-[#52526a] mb-0.5">Literal</p>
                    <p className="text-xs text-[#8b8ba0]">{annotation.literal_translation}</p>
                  </div>
                )}
                {annotation.ambiguity_notes.length > 0 && (
                  <div>
                    <p className="text-[10px] uppercase tracking-wider text-[#52526a] mb-0.5">Ambiguity</p>
                    <ul className="text-xs text-[#a1a1aa] space-y-0.5">
                      {annotation.ambiguity_notes.map((note, i) => (
                        <li key={i}>- {note}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {annotation.confidence > 0 && (
                  <p className="text-[10px] text-[#52526a]">
                    Confidence: {Math.round(annotation.confidence * 100)}%
                  </p>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
