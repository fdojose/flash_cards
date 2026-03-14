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

function playWithContext(notes) {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    console.debug('[Sound] ctx.state:', ctx.state);

    const play = () => {
      const now = ctx.currentTime;
      notes.forEach(([freq, offset, dur, vol]) => playNote(ctx, freq, now + offset, dur, vol));
    };

    if (ctx.state === 'suspended') {
      ctx.resume().then(play).catch(err => console.warn('[Sound] resume failed:', err));
    } else {
      play();
    }
  } catch (err) {
    console.warn('[Sound] AudioContext error:', err);
  }
}

/** Soft two-note ascending chime for correct answers */
export function useCorrectSound() {
  return useCallback(() => {
    playWithContext([
      [660, 0,    0.18, 0.18],   // E5
      [880, 0.12, 0.22, 0.18],   // A5 — ascending, pleasant
    ]);
  }, []);
}

/** Gentle single low tone for wrong answers — soft, not harsh */
export function useWrongSound() {
  return useCallback(() => {
    playWithContext([
      [220, 0, 0.28, 0.10],  // A3 — warm, low, quiet
    ]);
  }, []);
}
