<script lang="ts">
  import { onMount } from 'svelte';
  import {
    modelsStore,
    localModels,
    modelsBySource,
    searchResults,
    selectedRepo,
    selectedRepoFiles,
    downloads,
    modelsError,
    isSearching,
  } from './models';
  import type { LocalModel } from '../../shared/types';

  export let onSelect: (model: LocalModel) => void = () => {};

  let searchQuery = '';
  let urlInput = '';
  let activeTab: 'local' | 'download' = 'local';
  let searchTimeout: ReturnType<typeof setTimeout>;

  onMount(() => {
    modelsStore.loadModels();
    modelsStore.loadRecommended();
  });

  function handleSearch() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      modelsStore.searchHF(searchQuery);
    }, 300);
  }

  async function handleUrlPaste() {
    if (urlInput.trim()) {
      await modelsStore.parseHFUrl(urlInput.trim());
      urlInput = '';
    }
  }

  function handleDownload(filename: string) {
    if ($selectedRepo) {
      modelsStore.downloadModel($selectedRepo, filename);
    }
  }

  function formatBytes(bytes: number): string {
    if (bytes === 0) return 'Unknown size';
    const gb = bytes / (1024 ** 3);
    if (gb >= 1) return `${gb.toFixed(2)} GB`;
    const mb = bytes / (1024 ** 2);
    return `${mb.toFixed(0)} MB`;
  }

  function getSourceLabel(source: string): string {
    const labels: Record<string, string> = {
      llmlaunchpad: 'LLMLaunchpad',
      lm_studio: 'LM Studio',
      huggingface: 'HuggingFace Cache',
      gpt4all: 'GPT4All',
      jan: 'Jan.ai',
      ollama: 'Ollama',
    };
    return labels[source] || source;
  }

  function isDownloading(filename: string): boolean {
    return $downloads.some(
      (d) => d.filename === filename && (d.status === 'starting' || d.status === 'downloading')
    );
  }

  $: activeDownloads = $downloads.filter(
    (d) => d.status === 'starting' || d.status === 'downloading'
  );
</script>

<div class="bg-white dark:bg-gray-800 rounded-lg shadow">
  <!-- Tabs -->
  <div class="flex border-b dark:border-gray-700">
    <button
      on:click={() => activeTab = 'local'}
      class="flex-1 px-4 py-3 text-sm font-medium transition-colors {activeTab === 'local' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}"
    >
      Local Models ({$localModels.length})
    </button>
    <button
      on:click={() => activeTab = 'download'}
      class="flex-1 px-4 py-3 text-sm font-medium transition-colors {activeTab === 'download' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}"
    >
      Download
      {#if activeDownloads.length > 0}
        <span class="ml-1 px-1.5 py-0.5 text-xs bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 rounded-full">
          {activeDownloads.length}
        </span>
      {/if}
    </button>
  </div>

  <!-- Error display -->
  {#if $modelsError}
    <div class="m-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
      <div class="flex items-center justify-between">
        <span class="text-red-600 dark:text-red-400 text-sm">{$modelsError}</span>
        <button on:click={() => modelsStore.clearError()} class="text-red-400 hover:text-red-600">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  {/if}

  <!-- Local Models Tab -->
  {#if activeTab === 'local'}
    <div class="p-4">
      <!-- Refresh button -->
      <div class="flex justify-between items-center mb-4">
        <span class="text-sm text-gray-500">Select a model to use</span>
        <button
          on:click={() => modelsStore.scanModels()}
          class="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Rescan
        </button>
      </div>

      <!-- Models list grouped by source -->
      {#if $localModels.length === 0}
        <div class="text-center py-8 text-gray-400">
          <p>No models found</p>
          <p class="text-sm mt-2">Download a model or check your model directories</p>
        </div>
      {:else}
        <div class="space-y-4 max-h-96 overflow-y-auto">
          {#each Object.entries($modelsBySource) as [source, models]}
            <div>
              <h3 class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                {getSourceLabel(source)}
              </h3>
              <ul class="space-y-1">
                {#each models as model}
                  <li>
                    <button
                      on:click={() => onSelect(model)}
                      class="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    >
                      <div class="flex items-center justify-between">
                        <div class="min-w-0 flex-1">
                          <div class="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {model.name}
                          </div>
                          <div class="text-xs text-gray-500 flex gap-2">
                            <span>{formatBytes(model.size_bytes)}</span>
                            {#if model.quantization}
                              <span class="text-blue-500">{model.quantization}</span>
                            {/if}
                          </div>
                        </div>
                        <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                    </button>
                  </li>
                {/each}
              </ul>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {/if}

  <!-- Download Tab -->
  {#if activeTab === 'download'}
    <div class="p-4">
      <!-- URL input -->
      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Paste HuggingFace URL
        </label>
        <div class="flex gap-2">
          <input
            type="text"
            bind:value={urlInput}
            on:keydown={(e) => e.key === 'Enter' && handleUrlPaste()}
            placeholder="https://huggingface.co/..."
            class="flex-1 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none text-sm"
          />
          <button
            on:click={handleUrlPaste}
            class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm"
          >
            Go
          </button>
        </div>
      </div>

      <!-- Search -->
      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Or search HuggingFace
        </label>
        <div class="relative">
          <input
            type="text"
            bind:value={searchQuery}
            on:input={handleSearch}
            placeholder="Search for GGUF models..."
            class="w-full pl-9 pr-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none text-sm"
          />
          <svg class="absolute left-3 top-2.5 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          {#if $isSearching}
            <div class="absolute right-3 top-2.5">
              <svg class="w-4 h-4 animate-spin text-blue-500" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
              </svg>
            </div>
          {/if}
        </div>
      </div>

      <!-- Search results -->
      {#if $searchResults.length > 0 && !$selectedRepo}
        <div class="space-y-2 max-h-64 overflow-y-auto">
          {#each $searchResults as result}
            <button
              on:click={() => modelsStore.listRepoFiles(result.repo_id)}
              class="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <div class="text-sm font-medium text-gray-900 dark:text-white">
                {result.repo_id}
              </div>
              <div class="text-xs text-gray-500">
                {result.downloads.toLocaleString()} downloads
              </div>
            </button>
          {/each}
        </div>
      {/if}

      <!-- Selected repo files -->
      {#if $selectedRepo}
        <div class="mb-4">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-medium text-gray-900 dark:text-white">{$selectedRepo}</span>
            <button
              on:click={() => modelsStore.clearSelectedRepo()}
              class="text-sm text-gray-500 hover:text-gray-700"
            >
              Back
            </button>
          </div>
          <div class="space-y-2 max-h-64 overflow-y-auto">
            {#each $selectedRepoFiles as file}
              <div class="flex items-center justify-between px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-700">
                <div class="min-w-0 flex-1">
                  <div class="text-sm text-gray-900 dark:text-white truncate">{file.filename}</div>
                  <div class="text-xs text-gray-500">{formatBytes(file.size_bytes)}</div>
                </div>
                <button
                  on:click={() => handleDownload(file.filename)}
                  disabled={isDownloading(file.filename)}
                  class="ml-2 px-3 py-1 bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white rounded text-sm"
                >
                  {isDownloading(file.filename) ? 'Downloading...' : 'Download'}
                </button>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Active downloads -->
      {#if activeDownloads.length > 0}
        <div class="border-t dark:border-gray-700 pt-4 mt-4">
          <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Downloads</h3>
          <div class="space-y-2">
            {#each activeDownloads as download}
              <div class="px-3 py-2 rounded-lg bg-blue-50 dark:bg-blue-900/20">
                <div class="text-sm text-gray-900 dark:text-white truncate">{download.filename}</div>
                <div class="text-xs text-blue-600 dark:text-blue-400">
                  {download.status === 'starting' ? 'Starting...' : 'Downloading...'}
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>
