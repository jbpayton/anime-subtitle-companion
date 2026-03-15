import { useState, useRef, useCallback } from "react";

export interface PlaybackTimer {
  currentTimeMs: number;
  effectiveTimeMs: number;
  isPlaying: boolean;
  offsetMs: number;
  play: () => void;
  pause: () => void;
  toggle: () => void;
  seek: (ms: number) => void;
  adjustOffset: (deltaMs: number) => void;
  setOffset: (ms: number) => void;
}

export function usePlaybackTimer(): PlaybackTimer {
  const [currentTimeMs, setCurrentTimeMs] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [offsetMs, setOffsetMs] = useState(0);
  const rafRef = useRef<number | null>(null);
  const lastTickRef = useRef<number>(0);

  const tick = useCallback(() => {
    const now = performance.now();
    const delta = now - lastTickRef.current;
    lastTickRef.current = now;
    setCurrentTimeMs((prev) => prev + delta);
    rafRef.current = requestAnimationFrame(tick);
  }, []);

  const play = useCallback(() => {
    if (rafRef.current) return;
    lastTickRef.current = performance.now();
    rafRef.current = requestAnimationFrame(tick);
    setIsPlaying(true);
  }, [tick]);

  const pause = useCallback(() => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    setIsPlaying(false);
  }, []);

  const toggle = useCallback(() => {
    if (isPlaying) pause();
    else play();
  }, [isPlaying, play, pause]);

  const seek = useCallback((ms: number) => {
    setCurrentTimeMs(Math.max(0, ms));
  }, []);

  const adjustOffset = useCallback((deltaMs: number) => {
    setOffsetMs((prev) => prev + deltaMs);
  }, []);

  return {
    currentTimeMs,
    effectiveTimeMs: currentTimeMs + offsetMs,
    isPlaying,
    offsetMs,
    play,
    pause,
    toggle,
    seek,
    adjustOffset,
    setOffset: setOffsetMs,
  };
}
