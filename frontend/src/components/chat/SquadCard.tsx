"use client";

import type { SquadSummary } from "@/types/squads";

interface SquadCardProps {
  squad: SquadSummary;
  onClick: (code: string) => void;
}

export function SquadCard({ squad, onClick }: SquadCardProps) {
  return (
    <button
      onClick={() => onClick(squad.code)}
      className="w-full text-left bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 hover:border-zinc-600 rounded-xl p-4 transition-all group"
    >
      <div className="flex items-start gap-3">
        <span className="text-2xl flex-shrink-0 mt-0.5">{squad.icon}</span>
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-zinc-100 text-sm group-hover:text-white transition-colors">
            {squad.name}
          </div>
          <div className="text-zinc-400 text-xs mt-1 line-clamp-2">
            {squad.description}
          </div>
          <div className="flex items-center gap-3 mt-2">
            <span className="text-zinc-500 text-xs flex items-center gap-1">
              <span>👤</span>
              <span>{squad.agentCount} agents</span>
            </span>
            <span className="text-zinc-500 text-xs flex items-center gap-1">
              <span>📋</span>
              <span>{squad.stepCount} steps</span>
            </span>
          </div>
        </div>
      </div>
    </button>
  );
}
