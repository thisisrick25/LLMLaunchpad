<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from './shared/api';
  import type { Status, LocalModel, HardwareInfo } from './shared/types';

  // Feature components
  import ChatPanel from './features/chat/ChatPanel.svelte';
  import ChatSidebar from './features/chat/ChatSidebar.svelte';
  import { currentConversationId } from './features/chat/chat';
  import ServiceControls from './features/services/ServiceControls.svelte';
  import StatusBar from './features/services/StatusBar.svelte';
  import ModelSelector from './features/models/ModelSelector.svelte';
  import { localModels } from './features/models/models';

  // App state
  let status: Status | null = null;
  let hardware: HardwareInfo | null = null;
  let error: string | null = null;
  let loading = true;

  // UI state
  let showSidebar = true;
  let showControlsModal = false;
  let selectedModel: LocalModel | null = null;

  // Load initial status
  onMount(async () => {
    try {
      status = await api.getStatus();
      hardware = status?.hardware || null;
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to connect to backend';
    } finally {
      loading = false;
    }
  });

  function handleModelSelect(model: LocalModel) {
    selectedModel = model;
  }

  function toggleSidebar() {
    showSidebar = !showSidebar;
  }

  function toggleControlsModal() {
    showControlsModal = true;
  }

function closeControlsModal() {
    showControlsModal = false;
  }
</script>

<div class="h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
  <!-- Header -->
  <header class="bg-white dark:bg-gray-800 shadow-sm flex-shrink-0 z-10">
    <div class="px-4 py-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <!-- Sidebar toggle -->
          <button
            on:click={toggleSidebar}
            class="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            title={showSidebar ? 'Hide sidebar' : 'Show sidebar'}
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h7" />
            </svg>
          </button>
          <h1 class="text-xl font-bold text-gray-900 dark:text-white">
            LLMLaunchpad
          </h1>
        </div>

        <div class="flex items-center gap-3">
          <!-- Connection status -->
          {#if loading}
            <span class="flex items-center text-gray-500 text-sm">
              <span class="animate-pulse w-2 h-2 bg-yellow-400 rounded-full mr-2"></span>
              Connecting...
            </span>
          {:else if error}
            <span class="flex items-center text-red-500 text-sm">
              <span class="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
              Offline
            </span>
          {:else if status}
            <span class="flex items-center text-green-500 text-sm">
              <span class="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
              Connected
            </span>
          {/if}

          <!-- Right panel toggle -->
          <button
            on:click={toggleControlsModal}
            class="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            title='Show controls'
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </header>

  <!-- Main content area -->
  {#if loading}
    <div class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
        <p class="mt-4 text-gray-500 dark:text-gray-400">Connecting to backend...</p>
      </div>
    </div>
  {:else if error}
    <div class="flex-1 flex items-center justify-center p-8">
      <div class="max-w-md w-full bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
        <h2 class="text-lg font-semibold text-red-800 dark:text-red-200">Connection Error</h2>
        <p class="mt-2 text-red-600 dark:text-red-300">{error}</p>
        <p class="mt-4 text-sm text-red-500 dark:text-red-400">
          Make sure the backend server is running on http://localhost:8000
        </p>
        <button
          on:click={() => window.location.reload()}
          class="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm"
        >
          Retry
        </button>
      </div>
    </div>
  {:else}
    <div class="flex-1 flex overflow-hidden">
      <!-- Left Sidebar - Chat History -->
      {#if showSidebar}
        <aside class="w-72 flex-shrink-0 border-r dark:border-gray-700 overflow-hidden">
          <ChatSidebar currentConversationId={$currentConversationId} />
        </aside>
      {/if}

      <!-- Main Chat Panel -->
      <main class="flex-1 flex flex-col min-w-0 bg-white dark:bg-gray-800">
        <ChatPanel />
      </main>

      <!-- Right Panel - Controls -->
{#if showControlsModal}
        <div role="dialog" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" on:click|self={closeControlsModal}>
          <div class="bg-white dark:bg-gray-800 p-4 rounded-lg max-w-md w-full max-h-screen overflow-y-auto relative">
            <button class="absolute top-2 right-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-200" on:click={closeControlsModal} title="Close">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>

            <!-- Service Controls -->
            <ServiceControls
              models={$localModels}
              {selectedModel}
            />

            <!-- Model Selector -->
            <ModelSelector onSelect={handleModelSelect} />
          </div>
        </div>
      {/if}
    </div>
  {/if}

  <!-- Status Bar -->
  {#if status && !loading && !error}
    <footer class="flex-shrink-0">
      <StatusBar {hardware} />
    </footer>
  {/if}
</div>
