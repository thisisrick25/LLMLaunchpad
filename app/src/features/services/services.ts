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
}

// Initial state
const initialState: ServicesState = {
  serverStatus: null,
  mode: 'auto',
  availableModes: ['auto', 'gpu-heavy', 'cpu-only', 'cloud'],
  logs: [],
  isLoading: false,
  error: null,
};

// Create the store
function createServicesStore() {
  const { subscribe, set, update } = writable<ServicesState>(initialState);

  let logEventSource: EventSource | null = null;

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
