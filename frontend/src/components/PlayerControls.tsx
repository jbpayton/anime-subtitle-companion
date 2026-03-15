import type { PlaybackTimer } from "@/hooks/usePlaybackTimer";

function formatTime(ms: number): string {
  const totalSeconds = Math.floor(Math.abs(ms) / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  const centis = Math.floor((Math.abs(ms) % 1000) / 10);
  return `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}.${centis.toString().padStart(2, "0")}`;
}

interface Props {
  timer: PlaybackTimer;
  onUploadClick: () => void;
  hasSubtitles: boolean;
}

export function PlayerControls({ timer, onUploadClick, hasSubtitles }: Props) {
  return (
    <div className="flex items-center gap-4 px-4 py-3 bg-[#1a1a24] border-b border-[#2a2a3a]">
      <button
        onClick={onUploadClick}
        className="px-3 py-1.5 bg-[#6d28d9] hover:bg-[#7c3aed] rounded text-sm font-medium transition-colors"
      >
        Load Subtitles
      </button>

      <div className="w-px h-6 bg-[#2a2a3a]" />

      <button
        onClick={timer.toggle}
        disabled={!hasSubtitles}
        className="w-10 h-10 flex items-center justify-center bg-[#2a2a3a] hover:bg-[#3a3a4a] rounded-full disabled:opacity-40 transition-colors"
      >
        {timer.isPlaying ? "⏸" : "▶"}
      </button>

      <span className="font-mono text-sm text-[#a1a1aa] min-w-[80px]">
        {formatTime(timer.currentTimeMs)}
      </span>

      <div className="w-px h-6 bg-[#2a2a3a]" />

      <div className="flex items-center gap-2">
        <span className="text-xs text-[#71717a]">Offset:</span>
        <button
          onClick={() => timer.adjustOffset(-250)}
          className="px-2 py-1 bg-[#2a2a3a] hover:bg-[#3a3a4a] rounded text-xs transition-colors"
        >
          -250ms
        </button>
        <span className="font-mono text-sm text-[#a1a1aa] min-w-[70px] text-center">
          {timer.offsetMs >= 0 ? "+" : ""}{timer.offsetMs}ms
        </span>
        <button
          onClick={() => timer.adjustOffset(250)}
          className="px-2 py-1 bg-[#2a2a3a] hover:bg-[#3a3a4a] rounded text-xs transition-colors"
        >
          +250ms
        </button>
      </div>
    </div>
  );
}
