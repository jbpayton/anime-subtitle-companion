import { useEffect, useState } from "react";
import type { SubtitleSetInfo } from "@/types/subtitle";
import { listSubtitleSets } from "@/lib/api";

interface Props {
  onSelect: (set: SubtitleSetInfo) => void;
  onUploadClick: () => void;
  onClose: () => void;
}

export function SessionPicker({ onSelect, onUploadClick, onClose }: Props) {
  const [sets, setSets] = useState<SubtitleSetInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listSubtitleSets()
      .then(setSets)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
      <div
        className="bg-[#1a1a24] rounded-xl p-6 w-[520px] max-h-[70vh] border border-[#2a2a3a] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Subtitle Sessions</h2>
          <button
            onClick={onUploadClick}
            className="px-3 py-1.5 bg-[#6d28d9] hover:bg-[#7c3aed] rounded text-sm font-medium transition-colors"
          >
            Upload New
          </button>
        </div>

        {loading ? (
          <p className="text-sm text-[#71717a] py-8 text-center">Loading...</p>
        ) : sets.length === 0 ? (
          <p className="text-sm text-[#71717a] py-8 text-center">
            No subtitle files loaded yet. Upload one to get started.
          </p>
        ) : (
          <div className="flex-1 overflow-y-auto space-y-2">
            {sets.map((set) => (
              <button
                key={set.id}
                onClick={() => onSelect(set)}
                className="w-full text-left p-3 rounded-lg bg-[#0f0f14] hover:bg-[#2a2a3a] border border-[#2a2a3a] transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium truncate">{set.filename}</span>
                  <span className="text-xs text-[#52526a] shrink-0 ml-2">{set.block_count} blocks</span>
                </div>
                <p className="text-xs text-[#52526a] mt-1">{set.created_at}</p>
              </button>
            ))}
          </div>
        )}

        <button
          onClick={onClose}
          className="mt-4 text-sm text-[#71717a] hover:text-[#a1a1aa] transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
