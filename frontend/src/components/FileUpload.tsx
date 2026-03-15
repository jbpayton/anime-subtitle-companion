import { useRef, useState } from "react";
import { uploadSubtitle } from "@/lib/api";

interface Props {
  onUploaded: (subtitleSetId: string, filename: string, blockCount: number) => void;
  onClose: () => void;
}

export function FileUpload({ onUploaded, onClose }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  async function handleFile(file: File) {
    setUploading(true);
    setError(null);
    try {
      const result = await uploadSubtitle(file);
      onUploaded(result.subtitle_set_id, file.name, result.block_count);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
      <div
        className="bg-[#1a1a24] rounded-xl p-8 w-[480px] border border-[#2a2a3a]"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-lg font-semibold mb-4">Load Subtitle File</h2>

        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-colors ${
            dragOver ? "border-[#6d28d9] bg-[#6d28d9]/10" : "border-[#3a3a4a] hover:border-[#52526a]"
          }`}
        >
          <p className="text-[#a1a1aa] mb-1">
            {uploading ? "Uploading..." : "Drop .ass / .ssa / .srt file here"}
          </p>
          <p className="text-xs text-[#52526a]">or click to browse</p>
        </div>

        <input
          ref={inputRef}
          type="file"
          accept=".ass,.ssa,.srt"
          onChange={handleChange}
          className="hidden"
        />

        {error && <p className="mt-3 text-sm text-red-400">{error}</p>}

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
