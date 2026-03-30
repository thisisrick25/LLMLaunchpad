/**
 * Chat state management using Svelte stores.
 */

import { writable, derived, get } from 'svelte/store';
import { api } from '../../shared/api';
import type { ChatMessage, ConversationSummary, ConversationDetail, StreamChunk } from '../../shared/types';

// Types
interface ChatState {
  conversations: ConversationSummary[];
  currentConversationId: string | null;
  messages: ChatMessage[];
  isLoading: boolean;
  isStreaming: boolean;
  error: string | null;
  streamingContent: string;
}

  // Initial state
  const initialState: ChatState = {
    conversations: [
      {
        id: 'conv-1',
        title: 'Getting started with local AI',
        model: 'llama-3.1-8b-instruct',
        created_at: '2026-03-29T10:30:00Z',
        updated_at: '2026-03-29T10:35:00Z',
        message_count: 4
      },
      {
        id: 'conv-2',
        title: 'Python programming help',
        model: 'mistral-7b-instruct',
        created_at: '2026-03-28T14:20:00Z',
        updated_at: '2026-03-28T16:45:00Z',
        message_count: 12
      },
      {
        id: 'conv-3',
        title: 'Travel planning for Japan',
        model: 'phi-3-mini',
        created_at: '2026-03-27T09:15:00Z',
        updated_at: '2026-03-27T11:20:00Z',
        message_count: 8
      }
    ],
    currentConversationId: null,
    messages: [],
    isLoading: false,
    isStreaming: false,
    error: null,
    streamingContent: '',
  };

  // Search results state
  export const searchResults = writable<SearchResult[]>([]);

// Create the store
function createChatStore() {
  const { subscribe, set, update } = writable<ChatState>(initialState);

  return {
    subscribe,

    // Load conversations list
    async loadConversations() {
      update((s) => ({ ...s, isLoading: true, error: null }));
      try {
        const conversations = await api.getConversations();
        update((s) => ({ ...s, conversations, isLoading: false }));
      } catch (e) {
        update((s) => ({
          ...s,
          isLoading: false,
          error: e instanceof Error ? e.message : 'Failed to load conversations',
        }));
      }
    },

    // Load a specific conversation
    async loadConversation(id: string) {
      update((s) => ({ ...s, isLoading: true, error: null }));
      try {
        const detail = await api.getConversation(id);
        update((s) => ({
          ...s,
          currentConversationId: id,
          messages: detail.messages,
          isLoading: false,
        }));
      } catch (e) {
        update((s) => ({
          ...s,
          isLoading: false,
          error: e instanceof Error ? e.message : 'Failed to load conversation',
        }));
      }
    },

    // Start a new conversation
    newConversation() {
      update((s) => ({
        ...s,
        currentConversationId: null,
        messages: [],
        error: null,
      }));
    },

    // Send a message and stream the response
    async sendMessage(content: string) {
      const state = get({ subscribe });

      // Add user message
      const userMessage: ChatMessage = { role: 'user', content };
      update((s) => ({
        ...s,
        messages: [...s.messages, userMessage],
        isStreaming: true,
        streamingContent: '',
        error: null,
      }));

      try {
        // Build messages array with history
        const messages = [...state.messages, userMessage];

        // Stream the response
        let fullContent = '';
        let conversationId = state.currentConversationId;

        for await (const chunk of api.streamChat({
          messages,
          conversation_id: conversationId || undefined,
        })) {
          if (chunk.error) {
            throw new Error(chunk.error);
          }

          if (chunk.conversation_id && !conversationId) {
            conversationId = chunk.conversation_id;
            update((s) => ({ ...s, currentConversationId: conversationId }));
          }

          if (chunk.content) {
            fullContent += chunk.content;
            update((s) => ({ ...s, streamingContent: fullContent }));
          }

          if (chunk.done) {
            break;
          }
        }

        // Add assistant message
        const assistantMessage: ChatMessage = { role: 'assistant', content: fullContent };
        update((s) => ({
          ...s,
          messages: [...s.messages, assistantMessage],
          isStreaming: false,
          streamingContent: '',
        }));

        // Refresh conversations list
        this.loadConversations();
      } catch (e) {
        update((s) => ({
          ...s,
          isStreaming: false,
          streamingContent: '',
          error: e instanceof Error ? e.message : 'Failed to send message',
        }));
      }
    },

    // Delete a conversation
    async deleteConversation(id: string) {
      try {
        await api.deleteConversation(id);
        update((s) => {
          const newState = {
            ...s,
            conversations: s.conversations.filter((c) => c.id !== id),
          };
          // If we deleted the current conversation, clear it
          if (s.currentConversationId === id) {
            newState.currentConversationId = null;
            newState.messages = [];
          }
          return newState;
        });
      } catch (e) {
        update((s) => ({
          ...s,
          error: e instanceof Error ? e.message : 'Failed to delete conversation',
        }));
      }
    },

    // Update conversation title
    async updateTitle(id: string, title: string) {
      try {
        await api.updateConversationTitle(id, title);
        update((s) => ({
          ...s,
          conversations: s.conversations.map((c) => (c.id === id ? { ...c, title } : c)),
        }));
      } catch (e) {
        update((s) => ({
          ...s,
          error: e instanceof Error ? e.message : 'Failed to update title',
        }));
      }
    },

    // Search conversations
    async search(query: string) {
      try {
        const results = await api.searchConversations(query);
        searchResults.set(results);
        return results;
      } catch {
        searchResults.set([]);
        return [];
      }
    },

    // Export conversation
    async exportJSON(id: string) {
      const blob = await api.exportConversationJSON(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `conversation-${id.slice(0, 8)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    },

    async exportMarkdown(id: string) {
      const blob = await api.exportConversationMarkdown(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `conversation-${id.slice(0, 8)}.md`;
      a.click();
      URL.revokeObjectURL(url);
    },

    // Clear error
    clearError() {
      update((s) => ({ ...s, error: null }));
    },

    // Reset store
    reset() {
      set(initialState);
    },
  };
}

// Export the store
export const chatStore = createChatStore();

// Derived stores for convenience
export const conversations = derived(chatStore, ($s) => $s.conversations);
export const currentConversationId = derived(chatStore, ($s) => $s.currentConversationId);
export const currentMessages = derived(chatStore, ($s) => $s.messages);
export const isStreaming = derived(chatStore, ($s) => $s.isStreaming);
export const streamingContent = derived(chatStore, ($s) => $s.streamingContent);
export const chatError = derived(chatStore, ($s) => $s.error);
