<script lang="ts">
  import { onMount } from 'svelte';
  import { chatStore, conversations, searchResults } from './chat';
  import type { ConversationSummary } from '../../shared/types';
  import type { SearchResult } from '../../shared/types';

  export let currentConversationId: string | null = null;

  let searchQuery = '';
  let editingId: string | null = null;
  let editingTitle = '';
  let activeActionsId: string | null = null;

  function toggleActions(id: string) {
    if (activeActionsId === id) {
      activeActionsId = null;
    } else {
      activeActionsId = id;
    }
  }

  onMount(() => {
    chatStore.loadConversations();
  });

  function handleNewChat() {
    chatStore.newConversation();
  }

  function handleSelectConversation(id: string) {
    chatStore.loadConversation(id);
  }

  function handleSelectSearchResult(conversationId: string) {
    chatStore.loadConversation(conversationId);
    // Optionally, we could clear the search query after selecting a result
    // searchQuery = '';
  }

  function handleDelete(e: Event, id: string) {
    e.stopPropagation();
    if (confirm('Delete this conversation?')) {
      chatStore.deleteConversation(id);
    }
  }

  function startEditing(e: Event, conv: ConversationSummary) {
    e.stopPropagation();
    editingId = conv.id;
    editingTitle = conv.title;
  }

  function saveTitle() {
    if (editingId && editingTitle.trim()) {
      chatStore.updateTitle(editingId, editingTitle.trim());
    }
    editingId = null;
    editingTitle = '';
  }

  function handleEditKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') {
      e.preventDefault();
      saveTitle();
    } else if (e.key === 'Escape') {
      editingId = null;
      editingTitle = '';
    }
  }

  async function handleExport(e: Event, id: string, format: 'json' | 'md') {
    e.stopPropagation();
    if (format === 'json') {
      await chatStore.exportJSON(id);
    } else {
      await chatStore.exportMarkdown(id);
    }
  }

  function formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return date.toLocaleDateString();
  }

  // Trigger search when query changes
  $: if (searchQuery) {
      chatStore.search(searchQuery);
    } else {
      // Clear search results when query is empty
      searchResults.set([]);
    }
</script>

<div class="flex flex-col h-full bg-white dark:bg-black">
  <!-- Header -->
  <div class="p-3 border-b border-gray-200 dark:border-white/10">
    <button
      on:click={handleNewChat}
      class="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
      </svg>
      New Chat
    </button>
  </div>

  <!-- Search -->
  <div class="p-3 border-b border-gray-200 dark:border-white/10">
    <div class="relative">
      <input
        type="text"
        bind:value={searchQuery}
        placeholder="Search conversations..."
        class="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-white/20 bg-white dark:bg-black text-gray-900 dark:text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none"
      />
      <svg
        class="absolute left-3 top-2.5 w-4 h-4 text-gray-400"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    </div>
  </div>

  <!-- Conversations list -->
  <div class="flex-1 overflow-y-auto">
    {#if $searchResults.length === 0}
      {#if searchQuery}
        <div class="p-4 text-center text-gray-400 text-sm">
          No matching conversations
        </div>
      {:else}
        <div class="p-4 text-center text-gray-400 text-sm">
          No conversations yet
        </div>
      {/if}
    {:else}
      <ul class="py-2">
        {#each $searchResults as result (result.message_id)}
          <li class="mb-2">
            <div class="p-3 border rounded-lg hover:bg-gray-50 dark:hover:bg-white/5">
              <div class="flex items-start space-x-3">
                <div class="flex-shrink-0">
                  {#if result.role === 'user'}
                    <svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 01-7 7h14a7 7 0 01-7-7z" />
                    </svg>
                  {:else}
                    <svg class="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  {/if}
                </div>
                <div class="flex-1">
                  <div class="flex items-between justify-between mb-1">
                    <div class="text-sm font-medium">{#if result.conversation_title}{result.conversation_title}{:else}Untitled{/if}</div>
                    <div class="text-xs text-gray-500">{formatDate(result.created_at)}</div>
                  </div>
                  {#if result.content}
                    <div class="mt-1">
                      <p class="text-gray-700 dark:text-gray-200">
                        {@html result.content.replace(
                          new RegExp(searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi'),
                          match => `<mark class="bg-yellow-200">${match}</mark>`
                        )}
                      </p>
                    </div>
                  {/if}
                  <div class="mt-2 text-xs text-gray-500">
                    Message from {result.role === 'user' ? 'you' : 'assistant'} in conversation
                  </div>
                </div>
                <div class="mt-2 text-right">
                  <button
                    on:click={() => handleSelectSearchResult(result.conversation_id)}
                    class="text-sm font-medium text-blue-600 hover:text-blue-800"
                  >
                    View Conversation
                  </button>
                </div>
              </div>
            </div>
        {/each}
      </ul>
    {/if}
  </div>
</div>