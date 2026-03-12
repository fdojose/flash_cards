import { useCallback } from 'react';

function playNote(ctx, frequency, startTime, duration, volume = 0.18) {
  const oscillator = ctx.createOscillator();
  const gainNode = ctx.createGain();
  oscillator.connect(gainNode);
  gainNode.connect(ctx.destination);
  oscillator.type = 'sine';
  oscillator.frequency.setValueAtTime(frequency, startTime);
  gainNode.gain.setValueAtTime(0, startTime);
  gainNode.gain.linearRampToValueAtTime(volume, startTime + 0.01);
  gainNode.gain.exponentialRampToValueAtTime(0.001, startTime + duration);
  oscillator.start(startTime);
  oscillator.stop(startTime + duration);
}

/** Soft two-note ascending chime for correct answers */
export function useCorrectSound() {
  return useCallback(() => {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const now = ctx.currentTime;
      playNote(ctx, 660, now, 0.18);        // E5
      playNote(ctx, 880, now + 0.12, 0.22); // A5 — ascending, pleasant
    } catch { /* unavailable */ }
  }, []);
}

/** Gentle single low tone for wrong answers — soft, not harsh */
export function useWrongSound() {
  return useCallback(() => {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const now = ctx.currentTime;
      playNote(ctx, 220, now, 0.28, 0.10); // A3 — warm, low, quiet
    } catch { /* unavailable */ }
  }, []);
}
