import { useState, useCallback, useEffect, useRef } from "react";
import type { SubtitleBlock, AnnotatedBlock, Token, SubtitleSetInfo } from "@/types/subtitle";
import {
  getBlocks,
  getAnnotations,
  triggerAnnotation,
  getAnnotationStatus,
  type AnnotationStatus,
} from "@/lib/api";
import { usePlaybackTimer } from "@/hooks/usePlaybackTimer";
import { useActiveBlock } from "@/hooks/useActiveBlock";
import { PlayerControls } from "@/components/PlayerControls";
import { TranscriptView } from "@/components/TranscriptView";
import { SidePanel } from "@/components/SidePanel";
import { FileUpload } from "@/components/FileUpload";
import { SessionPicker } from "@/components/SessionPicker";

const LAST_SESSION_KEY = "asc_last_session";

export default function App() {
  const timer = usePlaybackTimer();

  const [blocks, setBlocks] = useState<SubtitleBlock[]>([]);
  const [annotations, setAnnotations] = useState<Map<string, AnnotatedBlock>>(new Map());
  const [subtitleSetId, setSubtitleSetId] = useState<string | null>(null);
  const [filename, setFilename] = useState<string>("");
  const [showUpload, setShowUpload] = useState(false);
  const [showSessionPicker, setShowSessionPicker] = useState(false);

  const [selectedBlockId, setSelectedBlockId] = useState<string | null>(null);
  const [selectedToken, setSelectedToken] = useState<Token | null>(null);

  const [annotationStatus, setAnnotationStatus] = useState<AnnotationStatus | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const activeBlockIndex = useActiveBlock(blocks, timer.effectiveTimeMs);

  // Load a subtitle set by ID (used for both new uploads and restoring sessions)
  const loadSession = useCallback(
    async (setId: string, name: string) => {
      setSubtitleSetId(setId);
      setFilename(name);
      setSelectedToken(null);
      setSelectedBlockId(null);

      const loadedBlocks = await getBlocks(setId);
      setBlocks(loadedBlocks);

      // Load existing annotations
      const existingAnnotations = await getAnnotations(setId);
      const map = new Map<string, AnnotatedBlock>();
      for (const a of existingAnnotations) {
        map.set(a.block_id, a);
      }
      setAnnotations(map);

      // Check if there's an active annotation job
      const status = await getAnnotationStatus(setId);
      setAnnotationStatus(status);
      if (status.status === "running") {
        startPolling(setId);
      }

      // Save to localStorage for resume
      localStorage.setItem(LAST_SESSION_KEY, JSON.stringify({ id: setId, filename: name }));

      timer.pause();
      timer.seek(0);
    },
    [timer],
  );

  // Poll for annotation progress
  const startPolling = useCallback((setId: string) => {
    if (pollRef.current) clearInterval(pollRef.current);

    pollRef.current = setInterval(async () => {
      try {
        const results = await getAnnotations(setId);
        const map = new Map<string, AnnotatedBlock>();
        for (const a of results) {
          map.set(a.block_id, a);
        }
        setAnnotations(map);

        const status = await getAnnotationStatus(setId);
        setAnnotationStatus(status);

        if (status.status === "complete" || status.status === "idle") {
          if (pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
          }
        }
      } catch (e) {
        console.error("Polling error:", e);
      }
    }, 5000);
  }, []);

  // Restore last session on mount
  useEffect(() => {
    const saved = localStorage.getItem(LAST_SESSION_KEY);
    if (saved) {
      try {
        const { id, filename: name } = JSON.parse(saved);
        if (id) loadSession(id, name);
      } catch {
        // Ignore invalid stored data
      }
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const handleUploaded = useCallback(
    async (setId: string, name: string, _blockCount: number) => {
      setShowUpload(false);
      setShowSessionPicker(false);
      await loadSession(setId, name);
    },
    [loadSession],
  );

  const handleSessionSelect = useCallback(
    async (set: SubtitleSetInfo) => {
      setShowSessionPicker(false);
      await loadSession(set.id, set.filename);
    },
    [loadSession],
  );

  const handleBlockClick = useCallback(
    (index: number) => {
      const block = blocks[index];
      if (!block) return;
      setSelectedBlockId(block.id);
      setSelectedToken(null);
      timer.seek(block.start_ms);
    },
    [blocks, timer],
  );

  const handleTokenSelect = useCallback(
    (token: Token, blockId: string) => {
      setSelectedToken(token);
      setSelectedBlockId(blockId);
    },
    [],
  );

  const handleAnnotate = useCallback(async () => {
    if (!subtitleSetId) return;
    try {
      await triggerAnnotation(subtitleSetId);
      startPolling(subtitleSetId);
      setAnnotationStatus({
        status: "running",
        annotated: annotations.size,
        total_blocks: blocks.length,
        errors: 0,
        current_batch: 0,
        total_batches: Math.ceil(blocks.length / 10),
      });
    } catch (e) {
      console.error("Failed to start annotation:", e);
    }
  }, [subtitleSetId, blocks.length, annotations.size, startPolling]);

  const isAnnotating = annotationStatus?.status === "running";

  const selectedAnnotation = selectedBlockId ? annotations.get(selectedBlockId) ?? null : null;
  const selectedBlock = selectedBlockId
    ? blocks.find((b) => b.id === selectedBlockId)
    : null;

  return (
    <div className="h-screen flex flex-col">
      <PlayerControls
        timer={timer}
        onUploadClick={() => setShowSessionPicker(true)}
        hasSubtitles={blocks.length > 0}
      />

      {blocks.length > 0 && (
        <div className="px-4 py-2 bg-[#1e1b2e] border-b border-[#2a2a3a] flex items-center gap-3">
          <span className="text-xs text-[#52526a] truncate max-w-[200px]" title={filename}>
            {filename}
          </span>
          <div className="w-px h-4 bg-[#2a2a3a]" />
          <button
            onClick={handleAnnotate}
            disabled={isAnnotating}
            className="px-3 py-1.5 bg-[#6d28d9] hover:bg-[#7c3aed] disabled:opacity-50 rounded text-sm font-medium transition-colors"
          >
            {isAnnotating ? "Annotating..." : annotations.size > 0 ? "Re-annotate" : "Annotate with AI"}
          </button>
          <span className="text-xs text-[#a1a1aa]">
            {isAnnotating ? (
              <>
                Batch {annotationStatus.current_batch}/{annotationStatus.total_batches}
                {" -- "}
                {annotations.size}/{blocks.length} blocks
                {annotationStatus.errors > 0 && ` (${annotationStatus.errors} errors)`}
              </>
            ) : annotations.size > 0 ? (
              <>{annotations.size}/{blocks.length} blocks annotated</>
            ) : (
              <>{blocks.length} blocks loaded</>
            )}
          </span>
          {isAnnotating && (
            <div className="flex-1 max-w-xs">
              <div className="h-1.5 bg-[#2a2a3a] rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#6d28d9] rounded-full transition-all duration-500"
                  style={{ width: `${blocks.length > 0 ? (annotations.size / blocks.length) * 100 : 0}%` }}
                />
              </div>
            </div>
          )}
        </div>
      )}

      <div className="flex-1 flex overflow-hidden">
        <TranscriptView
          blocks={blocks}
          annotations={annotations}
          activeBlockIndex={activeBlockIndex}
          selectedBlockId={selectedBlockId}
          selectedTokenSurface={selectedToken?.surface}
          onBlockClick={handleBlockClick}
          onTokenSelect={handleTokenSelect}
        />
        <SidePanel
          selectedToken={selectedToken}
          selectedAnnotation={selectedAnnotation}
          selectedBlockText={selectedBlock?.display_text ?? ""}
          sourceFilename={filename}
        />
      </div>

      {showSessionPicker && (
        <SessionPicker
          onSelect={handleSessionSelect}
          onUploadClick={() => {
            setShowSessionPicker(false);
            setShowUpload(true);
          }}
          onClose={() => setShowSessionPicker(false)}
        />
      )}

      {showUpload && (
        <FileUpload
          onUploaded={handleUploaded}
          onClose={() => setShowUpload(false)}
        />
      )}
    </div>
  );
}
