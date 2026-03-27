<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { servicesStore, serverState, isServerRunning, serviceLogs } from './services';
  import type { HardwareInfo } from '../../shared/types';

  export let hardware: HardwareInfo | null = null;

  let showLogs = false;
  let logsContainer: HTMLDivElement;

  onMount(() => {
    servicesStore.startLogStream();
  });

  onDestroy(() => {
    servicesStore.stopLogStream();
  });

  function getStateColor(state: string): string {
    switch (state) {
      case 'running':
        return 'text-green-500';
      case 'starting':
      case 'stopping':
        return 'text-yellow-500';
      case 'error':
        return 'text-red-500';
      default:
        return 'text-gray-400';
    }
  }

  function getStateIcon(state: string): string {
    switch (state) {
      case 'running':
        return 'M5 13l4 4L19 7'; // Check
      case 'starting':
      case 'stopping':
        return 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15'; // Refresh
      case 'error':
        return 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z'; // Warning
      default:
        return 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z'; // X Circle
    }
  }

  $: if (showLogs && logsContainer) {
    logsContainer.scrollTop = logsContainer.scrollHeight;
  }
</script>

<!-- Status Bar -->
<div class="bg-white dark:bg-black border-t border-gray-200 dark:border-white/10 text-gray-900 dark:text-white px-4 py-2 text-sm flex items-center justify-between">
  <div class="flex items-center gap-4">
    <!-- Server status -->
    <div class="flex items-center gap-2">
      <svg class="w-4 h-4 {getStateColor($serverState)}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={getStateIcon($serverState)} />
      </svg>
      <span class="text-gray-700 dark:text-gray-300">
        llama.cpp: <span class="{getStateColor($serverState)} font-medium">
          {$serverState === 'running' ? 'Running' : $serverState === 'stopped' ? 'Stopped' : $serverState}
        </span>
      </span>
    </div>

    <!-- Hardware info -->
    {#if hardware}
      <div class="flex items-center gap-4 text-gray-500 dark:text-gray-400 border-l border-gray-200 dark:border-white/10 pl-4">
        <span title={hardware.cpu_name}>
          CPU: {hardware.cpu_count} cores
        </span>
        <span>
          RAM: {hardware.ram_available_gb.toFixed(1)}/{hardware.ram_total_gb.toFixed(1)} GB
        </span>
        {#if hardware.has_gpu}
          <span>
            GPU: {hardware.total_vram_gb.toFixed(1)} GB VRAM
          </span>
        {/if}
      </div>
    {/if}
  </div>

  <!-- Log toggle -->
  <button
    on:click={() => showLogs = !showLogs}
    class="flex items-center gap-1 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
  >
    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
    </svg>
    <span>Logs</span>
    {#if $serviceLogs.length > 0}
      <span class="bg-gray-200 dark:bg-white/10 text-xs px-1.5 py-0.5 rounded-full">
        {$serviceLogs.length}
      </span>
    {/if}
  </button>
</div>

<!-- Log viewer panel -->
{#if showLogs}
  <div class="bg-white dark:bg-black border-t border-gray-200 dark:border-white/10">
    <div class="flex items-center justify-between px-4 py-2 border-b border-gray-200 dark:border-white/10">
      <span class="text-sm text-gray-500 dark:text-gray-400">Server Logs</span>
      <div class="flex items-center gap-2">
        <button
          on:click={() => servicesStore.clearLogs()}
          class="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
        >
          Clear
        </button>
        <button
          on:click={() => showLogs = false}
          class="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
    <div
      bind:this={logsContainer}
      class="h-48 overflow-y-auto p-4 font-mono text-xs text-gray-700 dark:text-gray-300"
    >
      {#if $serviceLogs.length === 0}
        <span class="text-gray-500">No logs yet...</span>
      {:else}
        {#each $serviceLogs as line}
          <div class="leading-relaxed {line.includes('[error]') || line.includes('Error') ? 'text-red-400' : line.includes('[warn]') ? 'text-yellow-400' : ''}">
            {line}
          </div>
        {/each}
      {/if}
    </div>
  </div>
{/if}
