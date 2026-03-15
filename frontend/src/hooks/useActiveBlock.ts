import { useMemo } from "react";
import type { SubtitleBlock } from "@/types/subtitle";

export function useActiveBlock(blocks: SubtitleBlock[], effectiveTimeMs: number): number {
  return useMemo(() => {
    if (blocks.length === 0) return -1;

    // Find the block that contains the effective time
    for (let i = 0; i < blocks.length; i++) {
      const block = blocks[i]!;
      if (effectiveTimeMs >= block.start_ms && effectiveTimeMs <= block.end_ms) {
        return i;
      }
    }

    // If between blocks, find the nearest upcoming block
    for (let i = 0; i < blocks.length; i++) {
      const block = blocks[i]!;
      if (block.start_ms > effectiveTimeMs) {
        // Return previous block if we're closer to it
        if (i > 0) {
          const prev = blocks[i - 1]!;
          const gapToPrev = effectiveTimeMs - prev.end_ms;
          const gapToNext = block.start_ms - effectiveTimeMs;
          return gapToPrev < gapToNext ? i - 1 : -1;
        }
        return -1;
      }
    }

    // Past the last block
    return blocks.length - 1;
  }, [blocks, effectiveTimeMs]);
}
