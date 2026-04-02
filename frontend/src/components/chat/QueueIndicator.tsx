"use client";

import type { SquadQueueItem } from "@/types/squads";

interface QueueIndicatorProps {
  items: SquadQueueItem[];
  onRemove: (id: string) => void;
}

export function QueueIndicator({ items, onRemove }: QueueIndicatorProps) {
  const queued = items.filter((item) => item.position > 1);

  if (queued.length === 0) return null;

  return (
    <div className="px-3 py-2 border-t border-zinc-800 bg-zinc-900/80">
      <div className="text-xs text-zinc-500 font-medium uppercase tracking-wider mb-1.5">
        Na Fila
      </div>
      <div className="flex flex-col gap-1">
        {queued.map((item) => (
          <div
            key={item.id}
            className="flex items-center justify-between gap-2 bg-zinc-800 rounded-lg px-3 py-1.5"
          >
            <div className="flex items-center gap-2 min-w-0">
              <span className="text-zinc-500 text-xs font-mono">#{item.position}</span>
              <span className="text-zinc-300 text-xs truncate">{item.squadName}</span>
            </div>
            <button
              onClick={() => onRemove(item.id)}
              className="text-zinc-600 hover:text-zinc-400 transition-colors flex-shrink-0 text-sm leading-none"
              title="Remover da fila"
            >
              ✕
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
