<script lang="ts">
  import { onMount } from 'svelte';
  import { chatStore, conversations } from './chat';
  import type { ConversationSummary } from '../../shared/types';

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
    {#if $conversations.length === 0}
      <div class="p-4 text-center text-gray-400 text-sm">
        {searchQuery ? 'No matching conversations' : 'No conversations yet'}
      </div>
    {:else}
      <ul class="py-2">
        {#each $conversations as conv (conv.id)}
          <li class="relative">
            <div class="flex w-full items-center py-3 px-3 {currentConversationId === conv.id ? 'bg-blue-50 dark:bg-blue-900/20' : ''} hover:bg-gray-100 dark:hover:bg-white/5">
              {#if editingId === conv.id}
                <input
                  type="text"
                  bind:value={editingTitle}
                  on:blur={saveTitle}
                  on:keydown={handleEditKeydown}
                  class="w-full px-2 py-1 text-sm rounded border border-blue-500 bg-white dark:bg-black text-gray-900 dark:text-white focus:outline-none"
                  autofocus
                />
              {:else}
                <div class="flex items-center justify-between">
                  <div class="flex-1">
                    <div class="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {conv.title}
                    </div>
                    <div class="text-xs text-gray-400 mt-0.5">
                      {formatDate(conv.updated_at)} · {conv.message_count} msgs
                    </div>
                  </div>
                  <!-- 3-dot menu button -->
                  <div class="relative">
                    <button
                      on:click|stopPropagation={() => toggleActions(conv.id)}
                      class="p-1.5 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 rounded-md"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12h.01M12 19h.01" />
                      </svg>
                    </button>

                    {#if activeActionsId === conv.id}
                      <div class="absolute right-0 mt-2 w-48 bg-white dark:bg-black border border-gray-200 dark:border-white/10 rounded-md shadow-lg z-20">
                        <div class="py-1">
                          <button
                            on:click={(e) => startEditing(e, conv)}
                            class="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10"
                          >
                            Rename
                          </button>
                          <button
                            on:click={(e) => handleExport(e, conv.id, 'md')}
                            class="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10"
                          >
                            Export
                          </button>
                          <div class="border-t border-gray-100 dark:border-white/5"></div>
                          <button
                            on:click={(e) => handleDelete(e, conv.id)}
                            class="w-full text-left px-3 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:red-900/20"
                          >
                            Delete
                          </button>
                        </div>
                      {/if}
                    </div>
                  {/if}
                </div>
              </div>
            </div>
          </li>
        {/each}
      </ul>
    {/if}
  </div>
</div>