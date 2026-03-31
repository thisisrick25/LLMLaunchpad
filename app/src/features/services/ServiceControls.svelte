<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import {
    servicesStore,
    serverStatus,
    serverState,
    isServerRunning,
    currentMode,
    servicesError,
    manualGpuLayers,
    vramUsage,
    vramTotal,
  } from './services';
  import type { LocalModel } from '../../shared/types';

  export let models: LocalModel[] = [];
  export let selectedModel: LocalModel | null = null;

  let contextSize = 4096;
  let showAdvanced = false;
  let manualGpuLayersOverride = '';

  onMount(() => {
    servicesStore.loadStatus();
    servicesStore.startVramMonitoring();
  });

  onDestroy(() => {
    servicesStore.stopVramMonitoring();
  });

  async function handleStart() {
    if (!selectedModel) return;
    const startRequest = {
      model: selectedModel.name,
      mode: $currentMode,
      context_size: contextSize,
    };
    
    // Add manual GPU layers override if set
    if ($manualGpuLayers !== null) {
      startRequest.gpu_layers = $manualGpuLayers;
    }
    
    await servicesStore.start(startRequest);
  }

  async function handleStop() {
    await servicesStore.stop();
  }

  async function handleRestart() {
    await servicesStore.restart();
  }

  async function handleModeChange(e: Event) {
    const target = e.target as HTMLSelectElement;
    await servicesStore.setMode(target.value);
  }

  function getStateColor(state: string): string {
    switch (state) {
      case 'running':
        return 'bg-green-500';
      case 'starting':
      case 'stopping':
        return 'bg-yellow-500 animate-pulse';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-400';
    }
  }

  function getStateText(state: string): string {
    switch (state) {
      case 'running':
        return 'Running';
      case 'starting':
        return 'Starting...';
      case 'stopping':
        return 'Stopping...';
      case 'error':
        return 'Error';
      default:
        return 'Stopped';
    }
  }

  function formatBytes(bytes: number): string {
    if (bytes === null || bytes === 0) return '0 GB';
    const gb = bytes / (1024 ** 3);
    return `${gb.toFixed(1)} GB`;
  }

  function formatVRAM(usage: number | null, total: number | null): string {
    if (usage === null || total === null || total === 0) return 'VRAM: N/A';
    const usageGB = usage / 1024;
    const totalGB = total / 1024;
    const percent = ((usage / total) * 100).toFixed(0);
    return `VRAM: ${usageGB.toFixed(1)} GB / ${totalGB.toFixed(1)} GB (${percent}%)`;
  }
</script>

<div class="bg-white dark:bg-black rounded-lg p-4">
  <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
    llama.cpp Server
  </h2>

  <!-- Status indicator -->
  <div class="flex items-center gap-3 mb-4">
    <span class="flex items-center gap-2">
      <span class="w-3 h-3 rounded-full {getStateColor($serverState)}"></span>
      <span class="text-gray-700 dark:text-gray-300">{getStateText($serverState)}</span>
    </span>
    {#if $serverStatus?.model_name}
      <span class="text-sm text-gray-500">
        ({$serverStatus.model_name})
      </span>
    {/if}
  </div>

  <!-- Error display -->
  {#if $servicesError}
    <div class="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
      <div class="flex items-center justify-between">
        <span class="text-red-600 dark:text-red-400 text-sm">{$servicesError}</span>
        <button
          on:click={() => servicesStore.clearError()}
          class="text-red-400 hover:text-red-600"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  {/if}

  <!-- Model selection (when stopped) -->
  {#if !$isServerRunning}
    <div class="space-y-4 mb-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Model
        </label>
        <select
          bind:value={selectedModel}
          class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:border-blue-500 focus:outline-none"
        >
          <option value={null}>Select a model...</option>
          {#each models as model}
            <option value={model}>
              {model.name} ({formatBytes(model.size_bytes)})
            </option>
          {/each}
        </select>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Performance Mode
        </label>
        <select
          value={$currentMode}
          on:change={handleModeChange}
          class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-white/20 bg-white dark:bg-black text-gray-900 dark:text-white focus:border-blue-500 focus:outline-none"
        >
          <option value="auto">Auto (Recommended)</option>
          <option value="gpu-heavy">GPU Heavy</option>
          <option value="cpu-only">CPU Only</option>
          <option value="cloud">Cloud</option>
        </select>
        <p class="mt-1 text-xs text-gray-500">
          {#if $currentMode === 'auto'}
            Automatically optimize based on available hardware
          {:else if $currentMode === 'gpu-heavy'}
            Maximize GPU usage (may use more VRAM)
          {:else if $currentMode === 'cpu-only'}
            Use CPU only (no GPU acceleration)
          {:else}
            Route to cloud providers
          {/if}
        </p>
      </div>

      <!-- Advanced options -->
      <button
        on:click={() => showAdvanced = !showAdvanced}
        class="text-sm text-blue-600 dark:text-blue-400 hover:underline"
      >
        {showAdvanced ? 'Hide' : 'Show'} advanced options
      </button>

       {#if showAdvanced}
         <div class="space-y-3 pl-2 border-l-2 border-gray-200 dark:border-white/10">
           <div>
             <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
               Context Size
             </label>
             <select
               bind:value={contextSize}
               class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-white/20 bg-white dark:bg-black text-gray-900 dark:text-white focus:border-blue-500 focus:outline-none"
             >
               <option value={2048}>2K</option>
               <option value={4096}>4K (Default)</option>
               <option value={8192}>8K</option>
               <option value={16384}>16K</option>
               <option value={32768}>32K</option>
             </select>
           </div>
           
           <div>
             <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
               Manual GPU Layers Override
             </label>
             <div class="flex items-center space-x-2">
               <input
                 type="number"
                 bind:value={manualGpuLayersOverride}
                 min="0"
                 max="200"
                 class="w-20 px-3 py-2 rounded-lg border border-gray-300 dark:border-white/20 bg-white dark:bg-black text-gray-900 dark:text-white focus:border-blue-500 focus:outline-none"
               />
               <span class="text-xs text-gray-500">layers</span>
               <button
                 on:click={() => {
                   servicesStore.setManualGpuLayers(manualGpuLayersOverride === '' ? null : parseInt(manualGpuLayersOverride));
                 }}
                 class="px-3 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded"
               >
                 Apply
               </button>
             </div>
             {#if $manualGpuLayers !== null}
               <p class="mt-1 text-xs text-green-600">
                 Manual override active: {$manualGpuLayers} GPU layers
               </p>
             {/if}
           </div>
           
           <div>
             <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
               VRAM Monitoring
             </label>
             <div class="space-y-1">
               <p class="text-xs text-gray-500">{formatVRAM($vramUsage, $vramTotal)}</p>
               {#if $vramUsage !== null && $vramTotal !== null}
                 <div class="w-full bg-gray-200 dark:bg-gray-700 rounded h-2">
                   <div
                     class="bg-blue-600 h-2 rounded"
                     style="width: {($vramUsage / $vramTotal) * 100}%"
                   ></div>
                 </div>
               {/if}
             </div>
           </div>
         </div>
       {/if}
    </div>
  {:else}
    <!-- Running server info -->
    <div class="mb-4 space-y-2 text-sm">
      {#if $serverStatus}
        <div class="flex justify-between">
          <span class="text-gray-500">GPU Layers:</span>
          <span class="text-gray-900 dark:text-white">{$serverStatus.gpu_layers}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-500">API URL:</span>
          <span class="text-gray-900 dark:text-white font-mono text-xs">
            {$serverStatus.api_url || 'N/A'}
          </span>
        </div>
      {/if}
    </div>
  {/if}

  <!-- Control buttons -->
  <div class="flex gap-2">
    {#if $isServerRunning}
      <button
        on:click={handleStop}
        disabled={$serverState === 'stopping'}
        class="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white rounded-lg text-sm font-medium transition-colors"
      >
        Stop
      </button>
      <button
        on:click={handleRestart}
        disabled={$serverState !== 'running'}
        class="px-4 py-2 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-400 text-white rounded-lg text-sm font-medium transition-colors"
      >
        Restart
      </button>
    {:else}
      <button
        on:click={handleStart}
        disabled={!selectedModel || $serverState === 'starting'}
        class="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-400 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
      >
        {$serverState === 'starting' ? 'Starting...' : 'Start Server'}
      </button>
    {/if}
  </div>
</div>
