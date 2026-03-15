import type { Token, AnnotatedBlock } from "@/types/subtitle";

interface Props {
  text: string;
  annotation?: AnnotatedBlock;
  onTokenSelect: (token: Token) => void;
  selectedTokenSurface?: string;
}

export function SubtitleLine({ text, annotation, onTokenSelect, selectedTokenSurface }: Props) {
  if (!annotation || annotation.tokens.length === 0) {
    return <div className="text-lg leading-relaxed">{text}</div>;
  }

  return (
    <div className="space-y-1">
      {/* Interlinear token display */}
      <div className="flex flex-wrap gap-x-1 gap-y-2 items-end">
        {annotation.tokens.map((token, i) => {
          const isSelected = selectedTokenSurface === token.surface;
          const showReading = token.reading && token.reading !== token.surface;

          return (
            <span
              key={i}
              onClick={(e) => { e.stopPropagation(); onTokenSelect(token); }}
              className={`inline-flex flex-col items-center cursor-pointer rounded px-1 py-0.5 transition-colors ${
                isSelected
                  ? "bg-[#6d28d9]/40 text-[#c4b5fd]"
                  : "hover:bg-[#6d28d9]/20"
              }`}
            >
              {/* Reading (furigana) above */}
              {showReading && (
                <span className="text-[10px] text-[#8b8ba0] leading-none mb-0.5">
                  {token.reading}
                </span>
              )}
              {/* Surface form */}
              <span className="text-lg leading-tight">{token.surface}</span>
              {/* Gloss below */}
              <span className="text-[10px] text-[#6d6d8a] leading-none mt-0.5 max-w-[120px] text-center truncate">
                {token.gloss}
              </span>
            </span>
          );
        })}
      </div>

      {/* Conjugation / grammar chips for notable tokens */}
      {annotation.tokens.some(t => t.conjugation) && (
        <div className="flex flex-wrap gap-1 mt-1">
          {annotation.tokens
            .filter(t => t.conjugation)
            .map((t, i) => (
              <span
                key={i}
                className="text-[10px] px-1.5 py-0.5 bg-[#2a2a3a] text-[#a78bfa] rounded"
              >
                {t.surface}: {t.conjugation}
              </span>
            ))}
        </div>
      )}
    </div>
  );
}
