<script lang="ts">
  import { onMount, afterUpdate, tick } from 'svelte';
  import { chatStore, currentMessages, isStreaming, streamingContent, chatError } from './chat';
  import type { ChatMessage } from '../../shared/types';
  import DOMPurify from 'dompurify';

  let inputValue = '';
  let messagesContainer: HTMLDivElement;
  let inputElement: HTMLTextAreaElement;

  // Auto-scroll to bottom when new messages arrive
  afterUpdate(() => {
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  });

  // Focus input on mount
  onMount(() => {
    inputElement?.focus();
  });

  async function handleSubmit() {
    const content = inputValue.trim();
    if (!content || $isStreaming) return;

    inputValue = '';
    await chatStore.sendMessage(content);
    await tick();
    inputElement?.focus();
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

   function formatContent(content: string): string {
     // Basic markdown-like formatting
     // Convert code blocks
     content = content.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>');
     // Convert inline code
     content = content.replace(/`([^`]+)`/g, '<code>$1</code>');
     // Convert newlines to <br> (outside of pre blocks)
     content = content.replace(/\n/g, '<br>');
     // Sanitize HTML to prevent XSS
     return DOMPurify.sanitize(content);
   }
</script>

<div class="flex flex-col h-full">
  <!-- Messages area -->
  <div
    bind:this={messagesContainer}
    class="flex-1 overflow-y-auto p-4 space-y-4"
  >
    {#if $currentMessages.length === 0 && !$isStreaming}
      <div class="flex items-center justify-center h-full text-gray-400">
        <div class="text-center">
          <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <p class="text-lg">Start a new conversation</p>
          <p class="text-sm mt-1">Type a message below to begin</p>
        </div>
      </div>
    {:else}
      {#each $currentMessages as message (message.id || message.content)}
        <div class="flex {message.role === 'user' ? 'justify-end' : 'justify-start'}">
          <div
            class="max-w-[80%] rounded-lg px-4 py-2 {message.role === 'user'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 dark:bg-white/10 text-gray-900 dark:text-white'}"
          >
            <div class="text-xs opacity-70 mb-1">
              {message.role === 'user' ? 'You' : 'Assistant'}
            </div>
            <div class="prose prose-sm dark:prose-invert max-w-none">
              {@html formatContent(message.content)}
            </div>
          </div>
        </div>
      {/each}

      <!-- Streaming message -->
      {#if $isStreaming}
        <div class="flex justify-start">
          <div class="max-w-[80%] rounded-lg px-4 py-2 bg-gray-100 dark:bg-white/10 text-gray-900 dark:text-white">
            <div class="text-xs opacity-70 mb-1">Assistant</div>
            <div class="prose prose-sm dark:prose-invert max-w-none">
              {#if $streamingContent}
                {@html formatContent($streamingContent)}
              {/if}
              <span class="inline-block w-2 h-4 bg-gray-400 animate-pulse ml-1"></span>
            </div>
          </div>
        </div>
      {/if}
    {/if}
  </div>

  <!-- Error display -->
  {#if $chatError}
    <div class="mx-4 mb-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
      <div class="flex items-center justify-between">
        <span class="text-red-600 dark:text-red-400 text-sm">{$chatError}</span>
        <button
          on:click={() => chatStore.clearError()}
          class="text-red-400 hover:text-red-600"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  {/if}

  <!-- Input area -->
  <div class="border-t border-gray-200 dark:border-white/10 p-4">
    <form on:submit|preventDefault={handleSubmit} class="flex gap-2">
      <textarea
        bind:this={inputElement}
        bind:value={inputValue}
        on:keydown={handleKeyDown}
        placeholder="Type a message... (Enter to send, Shift+Enter for new line)"
        disabled={$isStreaming}
        rows="1"
        class="flex-1 resize-none rounded-lg border border-gray-300 dark:border-white/20 bg-white dark:bg-black px-4 py-2 text-gray-900 dark:text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
      ></textarea>
      <button
        type="submit"
        disabled={!inputValue.trim() || $isStreaming}
        class="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
      >
        {#if $isStreaming}
          <svg class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        {:else}
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        {/if}
      </button>
    </form>
  </div>
</div>
