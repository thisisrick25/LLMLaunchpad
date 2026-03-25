/**
 * Models state management using Svelte stores.
 */

import { writable, derived } from 'svelte/store';
import { api } from '../../shared/api';
import type { LocalModel, HFSearchResult, HFModelFile, RecommendedModel, DownloadStatus } from '../../shared/types';

// Types
interface ModelsState {
  localModels: LocalModel[];
  recommendedModels: RecommendedModel[];
  searchResults: HFSearchResult[];
  selectedRepoFiles: HFModelFile[];
  selectedRepo: string | null;
  downloads: DownloadStatus[];
  isLoading: boolean;
  isSearching: boolean;
  error: string | null;
}

// Initial state
const initialState: ModelsState = {
  localModels: [],
  recommendedModels: [],
  searchResults: [],
  selectedRepoFiles: [],
  selectedRepo: null,
  downloads: [],
  isLoading: false,
  isSearching: false,
  error: null,
};

// Create the store
function createModelsStore() {
  const { subscribe, set, update } = writable<ModelsState>(initialState);

  // Poll downloads periodically
  let downloadPollInterval: ReturnType<typeof setInterval> | null = null;

  return {
    subscribe,

    // Load local models
    async loadModels(refresh = false) {
      update((s) => ({ ...s, isLoading: true, error: null }));
      try {
        const response = await api.getModels(refresh);
        update((s) => ({ ...s, localModels: response.models, isLoading: false }));
      } catch (e) {
        update((s) => ({
          ...s,
          isLoading: false,
          error: e instanceof Error ? e.message : 'Failed to load models',
        }));
      }
    },

    // Scan for models
    async scanModels() {
      update((s) => ({ ...s, isLoading: true, error: null }));
      try {
        const response = await api.scanModels();
        update((s) => ({ ...s, localModels: response.models, isLoading: false }));
      } catch (e) {
        update((s) => ({
          ...s,
          isLoading: false,
          error: e instanceof Error ? e.message : 'Failed to scan models',
        }));
      }
    },

    // Load recommended models
    async loadRecommended() {
      try {
        const response = await api.getRecommendedModels();
        update((s) => ({ ...s, recommendedModels: response.models }));
      } catch (e) {
        // Silently fail for recommended models
      }
    },

    // Search HuggingFace
    async searchHF(query: string) {
      if (!query.trim()) {
        update((s) => ({ ...s, searchResults: [] }));
        return;
      }

      update((s) => ({ ...s, isSearching: true, error: null }));
      try {
        const response = await api.searchHF(query);
        update((s) => ({ ...s, searchResults: response.results, isSearching: false }));
      } catch (e) {
        update((s) => ({
          ...s,
          isSearching: false,
          error: e instanceof Error ? e.message : 'Search failed',
        }));
      }
    },

    // List files in a HF repo
    async listRepoFiles(repoId: string) {
      update((s) => ({ ...s, isLoading: true, selectedRepo: repoId, selectedRepoFiles: [] }));
      try {
        const response = await api.listHFFiles(repoId);
        update((s) => ({ ...s, selectedRepoFiles: response.files, isLoading: false }));
      } catch (e) {
        update((s) => ({
          ...s,
          isLoading: false,
          error: e instanceof Error ? e.message : 'Failed to list files',
        }));
      }
    },

    // Clear selected repo
    clearSelectedRepo() {
      update((s) => ({ ...s, selectedRepo: null, selectedRepoFiles: [] }));
    },

    // Download a model
    async downloadModel(repoId: string, filename: string) {
      try {
        await api.downloadModel(repoId, filename);
        // Start polling for download status
        this.startDownloadPolling();
      } catch (e) {
        update((s) => ({
          ...s,
          error: e instanceof Error ? e.message : 'Download failed',
        }));
      }
    },

    // Poll download status
    async pollDownloads() {
      try {
        const response = await api.getDownloads();
        update((s) => ({ ...s, downloads: response.downloads }));

        // Check if any downloads are in progress
        const hasActive = response.downloads.some(
          (d) => d.status === 'starting' || d.status === 'downloading'
        );

        // If no active downloads, stop polling and refresh models
        if (!hasActive && downloadPollInterval) {
          this.stopDownloadPolling();
          // Refresh model list if any completed
          if (response.downloads.some((d) => d.status === 'completed')) {
            this.loadModels(true);
          }
        }
      } catch {
        // Ignore polling errors
      }
    },

    // Start polling downloads
    startDownloadPolling() {
      if (downloadPollInterval) return;
      this.pollDownloads();
      downloadPollInterval = setInterval(() => this.pollDownloads(), 2000);
    },

    // Stop polling downloads
    stopDownloadPolling() {
      if (downloadPollInterval) {
        clearInterval(downloadPollInterval);
        downloadPollInterval = null;
      }
    },

    // Parse a HF URL
    async parseHFUrl(url: string) {
      try {
        const result = await api.parseHFUrl(url);
        if (result.repo_id) {
          await this.listRepoFiles(result.repo_id);
        }
        return result;
      } catch (e) {
        update((s) => ({
          ...s,
          error: e instanceof Error ? e.message : 'Invalid URL',
        }));
        return null;
      }
    },

    // Clear error
    clearError() {
      update((s) => ({ ...s, error: null }));
    },

    // Clear search
    clearSearch() {
      update((s) => ({ ...s, searchResults: [], selectedRepo: null, selectedRepoFiles: [] }));
    },

    // Reset store
    reset() {
      this.stopDownloadPolling();
      set(initialState);
    },
  };
}

// Export the store
export const modelsStore = createModelsStore();

// Derived stores for convenience
export const localModels = derived(modelsStore, ($s) => $s.localModels);
export const recommendedModels = derived(modelsStore, ($s) => $s.recommendedModels);
export const searchResults = derived(modelsStore, ($s) => $s.searchResults);
export const selectedRepoFiles = derived(modelsStore, ($s) => $s.selectedRepoFiles);
export const selectedRepo = derived(modelsStore, ($s) => $s.selectedRepo);
export const downloads = derived(modelsStore, ($s) => $s.downloads);
export const modelsError = derived(modelsStore, ($s) => $s.error);
export const isSearching = derived(modelsStore, ($s) => $s.isSearching);

// Group models by source
export const modelsBySource = derived(localModels, ($models) => {
  const grouped: Record<string, LocalModel[]> = {};
  for (const model of $models) {
    const source = model.source || 'unknown';
    if (!grouped[source]) {
      grouped[source] = [];
    }
    grouped[source].push(model);
  }
  return grouped;
});
