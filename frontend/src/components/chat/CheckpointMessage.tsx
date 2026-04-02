"use client";

import { useState, useEffect } from "react";

interface CheckpointMessageProps {
  stepName: string;
  content: string;
  onApprove: () => void;
  onAdjust: (feedback: string) => void;
  isResolved?: boolean;
}

export function CheckpointMessage({
  stepName,
  content,
  onApprove,
  onAdjust,
  isResolved = false,
}: CheckpointMessageProps) {
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState("");

  useEffect(() => {
    // Play a subtle "pling" sound via Web Audio API
    try {
      const AudioContextClass =
        window.AudioContext ||
        (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
      if (!AudioContextClass) return;
      const ctx = new AudioContextClass();
      const oscillator = ctx.createOscillator();
      const gainNode = ctx.createGain();
      oscillator.connect(gainNode);
      gainNode.connect(ctx.destination);
      oscillator.frequency.setValueAtTime(880, ctx.currentTime);
      oscillator.type = "sine";
      gainNode.gain.setValueAtTime(0.1, ctx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
      oscillator.start(ctx.currentTime);
      oscillator.stop(ctx.currentTime + 0.3);
    } catch {
      // Web Audio not available, ignore
    }
  }, []);

  const handleAdjust = () => {
    const trimmed = feedback.trim();
    if (!trimmed) return;
    onAdjust(trimmed);
    setShowFeedback(false);
    setFeedback("");
  };

  return (
    <div className="mx-4 my-2 border border-amber-700/60 bg-amber-950/30 rounded-xl overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-2 bg-amber-900/30 border-b border-amber-700/40">
        <span className="text-amber-400">⏸</span>
        <span className="text-amber-300 text-xs font-semibold uppercase tracking-wider">
          Checkpoint: {stepName}
        </span>
      </div>

      <div className="px-4 py-3">
        <p className="text-zinc-200 text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
      </div>

      {!isResolved && (
        <div className="px-4 pb-4">
          {!showFeedback ? (
            <div className="flex gap-2">
              <button
                onClick={onApprove}
                className="flex-1 bg-emerald-700 hover:bg-emerald-600 text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors"
              >
                Aprovar
              </button>
              <button
                onClick={() => setShowFeedback(true)}
                className="flex-1 bg-zinc-700 hover:bg-zinc-600 text-zinc-200 rounded-lg px-4 py-2 text-sm font-medium transition-colors"
              >
                Pedir Ajuste
              </button>
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              <textarea
                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-amber-600 focus:ring-1 focus:ring-amber-600 resize-none min-h-[80px]"
                placeholder="Descreva o ajuste desejado..."
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                autoFocus
              />
              <div className="flex gap-2">
                <button
                  onClick={handleAdjust}
                  disabled={!feedback.trim()}
                  className="flex-1 bg-amber-700 hover:bg-amber-600 disabled:bg-zinc-700 disabled:cursor-not-allowed text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors"
                >
                  Enviar Ajuste
                </button>
                <button
                  onClick={() => {
                    setShowFeedback(false);
                    setFeedback("");
                  }}
                  className="bg-zinc-700 hover:bg-zinc-600 text-zinc-300 rounded-lg px-4 py-2 text-sm font-medium transition-colors"
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {isResolved && (
        <div className="px-4 pb-3">
          <span className="text-emerald-400 text-xs font-medium flex items-center gap-1">
            <span>✓</span>
            <span>Resolvido</span>
          </span>
        </div>
      )}
    </div>
  );
}
