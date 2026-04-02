import { create } from "zustand";
import type { PipelineState, PipelineStepStatus, SquadQueueItem, SquadSummary } from "@/types/squads";

interface SquadState {
  squads: SquadSummary[];
  pipelineState: PipelineState | null;
  queue: SquadQueueItem[];
  setSquads: (squads: SquadSummary[]) => void;
  setPipelineState: (state: PipelineState | null) => void;
  setQueue: (queue: SquadQueueItem[]) => void;
  updateStepStatus: (stepId: string, status: PipelineStepStatus) => void;
}

export const useSquadStore = create<SquadState>((set) => ({
  squads: [],
  pipelineState: null,
  queue: [],
  setSquads: (squads) => set({ squads }),
  setPipelineState: (pipelineState) => set({ pipelineState }),
  setQueue: (queue) => set({ queue }),
  updateStepStatus: (stepId, status) =>
    set((state) => {
      if (!state.pipelineState) return state;
      return {
        pipelineState: {
          ...state.pipelineState,
          stepStates: { ...state.pipelineState.stepStates, [stepId]: status },
        },
      };
    }),
}));
