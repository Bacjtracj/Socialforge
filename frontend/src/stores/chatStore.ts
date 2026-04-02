import { create } from "zustand";
import type { ChatMessage } from "@/types/squads";

let messageCounter = 0;

interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  addMessage: (msg: ChatMessage) => void;
  setLoading: (loading: boolean) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isLoading: false,
  addMessage: (msg) =>
    set((state) => ({
      messages: [...state.messages, { ...msg, id: msg.id || `msg-${++messageCounter}` }],
    })),
  setLoading: (isLoading) => set({ isLoading }),
  clearMessages: () => set({ messages: [] }),
}));
