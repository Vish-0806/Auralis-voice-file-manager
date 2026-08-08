import { create } from 'zustand';
import { AssistantState } from '../types';

const initialState = {
  conversationId: null,
  messages: [],
  isStreaming: false,
  status: 'idle' as const,
  error: null,
};

export const useAssistantStore = create<AssistantState>()((set) => ({
  ...initialState,
  setConversationId: (value) => set({ conversationId: value }),
  addMessage: (msg) => set((state) => {
    const newMessage = {
      ...msg,
      id: Math.random().toString(36).substring(2, 11),
      timestamp: Date.now(),
    };
    return { messages: [...state.messages, newMessage] };
  }),
  updateMessage: (id, updates) => set((state) => ({
    messages: state.messages.map((m) => m.id === id ? { ...m, ...updates } : m)
  })),
  setStreaming: (value) => set({ isStreaming: value }),
  setStatus: (status) => set({ status }),
  setError: (error) => set({ error }),
  clearConversation: () => set({ conversationId: null, messages: [], error: null, status: 'idle' }),
  reset: () => set(initialState),
}));
