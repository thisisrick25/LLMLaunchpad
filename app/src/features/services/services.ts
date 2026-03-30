/**
 * Services state management using Svelte stores.
 */

import { writable, derived } from 'svelte/store';
import { api } from '../../shared/api';
import type { LlamaServerStatus, StartRequest } from '../../shared/types';

// Types
interface ServicesState {
  serverStatus: LlamaServerStatus | null;
  mode: string;
  availableModes: string[];
  logs: string[];
  isLoading: boolean;
  error: string | null;
  manualGpuLayers: number | null;
  vramUsage: number | null;
  vramTotal: number | null;
}

// Initial state
const initialState: ServicesState = {
  serverStatus: null,
  mode: 'auto',
  availableModes: ['auto', 'gpu-heavy', 'cpu-only', 'cloud'],
  logs: [],
  isLoading: false,
  error: null,
  manualGpuLayers: null,
  vramUsage: null,
  vramTotal: null,
};

// Create the store
function createServicesStore() {
  const { subscribe, set, update } = writable<ServicesState>(initialState);

  let logEventSource: EventSource | null = null;
  let vramPollingInterval: number | null = null;

  return {
    subscribe,

    // Load server status
    async loadStatus() {
      update((s) => ({ ...s, isLoading: true, error: null }));
      try {
        const [serverStatus, modeInfo] = await Promise.all([
          api.getServerStatus(),
          api.getMode(),
        ]);
        update((s) => ({
          ...s,
          serverStatus,
          mode: modeInfo.mode,
          availableModes: modeInfo.available_modes,
          isLoading: false,
        }));
      } catch (e) {
        update((s) => ({
          ...s,
          isLoading: false,
          error: e instanceof Error ? e.message : 'Failed to load status',
        }));
      }
    },

    // Start the server
    async start(req: StartRequest) {
      update((s) => ({ ...s, isLoading: true, error: null }));
      try {
        await api.startServer(req);
        // Refresh status after starting
        await this.loadStatus();
      } catch (e) {
        update((s) => ({
          ...s,
          isLoading: false,
          error: e instanceof Error ? e.message : 'Failed to start server',
        }));
      }
    },

    // Stop the server
    async stop() {
      update((s) => ({ ...s, isLoading: true, error: null }));
      try {
        await api.stopServer();
        await this.loadStatus();
      } catch (e) {
        update((s) => ({
          ...s,
          isLoading: false,
          error: e instanceof Error ? e.message : 'Failed to stop server',
        }));
      }
    },

    // Restart the server
    async restart() {
      update((s) => ({ ...s, isLoading: true, error: null }));
      try {
        await api.restartServer();
        await this.loadStatus();
      } catch (e) {
        update((s) => ({
          ...s,
          isLoading: false,
          error: e instanceof Error ? e.message : 'Failed to restart server',
        }));
      }
    },

    // Set performance mode
    async setMode(mode: string) {
      update((s) => ({ ...s, isLoading: true, error: null }));
      try {
        await api.setMode(mode);
        update((s) => ({ ...s, mode, isLoading: false }));
      } catch (e) {
        update((s) => ({
          ...s,
          isLoading: false,
          error: e instanceof Error ? e.message : 'Failed to set mode',
        }));
      }
    },

    // Set manual GPU layers override
    setManualGpuLayers(layers: number | null) {
      update((s) => ({ ...s, manualGpuLayers: layers }));
    },

    // Start VRAM monitoring
    startVramMonitoring() {
      // Poll every 5 seconds
      vramPollingInterval = setInterval(async () => {
        try {
          const hardware = await api.getHardware();
          update((s) => ({
            ...s,
            vramTotal: hardware.total_vram_gb * 1024, // Convert to MB
            vramUsage: hardware.total_vram_gb * 1024 - hardware.ram_available_gb * 1024, // Approximate VRAM usage
          }));
        } catch (error) {
          // Silently ignore VRAM monitoring errors to avoid spamming
          console.debug('VRAM monitoring error:', error);
        }
      }, 5000);
    },

    // Stop VRAM monitoring
    stopVramMonitoring() {
      if (vramPollingInterval) {
        clearInterval(vramPollingInterval);
        vramPollingInterval = null;
      }
    },

    // Start streaming logs
    startLogStream() {
      if (logEventSource) {
        logEventSource.close();
      }

      logEventSource = api.streamLogs((data) => {
        if (data.type === 'log' && data.data) {
          update((s) => ({
            ...s,
            logs: [...s.logs.slice(-500), data.data], // Keep last 500 lines
          }));
        } else if (data.type === 'status' && data.data) {
          update((s) => ({ ...s, serverStatus: data.data }));
        }
      });

      logEventSource.onerror = () => {
        // Will automatically reconnect
      };
    },

    // Stop streaming logs
    stopLogStream() {
      if (logEventSource) {
        logEventSource.close();
        logEventSource = null;
      }
    },

    // Clear logs
    clearLogs() {
      update((s) => ({ ...s, logs: [] }));
    },

    // Clear error
    clearError() {
      update((s) => ({ ...s, error: null }));
    },

    // Reset store
    reset() {
      this.stopLogStream();
      this.stopVramMonitoring();
      set(initialState);
    },
  };
}

// Export the store
export const servicesStore = createServicesStore();

// Derived stores for convenience
export const serverStatus = derived(servicesStore, ($s) => $s.serverStatus);
export const serverState = derived(servicesStore, ($s) => $s.serverStatus?.state ?? 'stopped');
export const isServerRunning = derived(servicesStore, ($s) => $s.serverStatus?.state === 'running');
export const currentMode = derived(servicesStore, ($s) => $s.mode);
export const serviceLogs = derived(servicesStore, ($s) => $s.logs);
export const servicesError = derived(servicesStore, ($s) => $s.error);
export const manualGpuLayers = derived(servicesStore, ($s) => $s.manualGpuLayers);
export const vramUsage = derived(servicesStore, ($s) => $s.vramUsage);
export const vramTotal = derived(servicesStore, ($s) => $s.vramTotal);
