/**
 * API client for communicating with the backend.
 */

import type {
  Status,
  HardwareInfo,
  LocalModel,
  HFSearchResult,
  HFModelFile,
  RecommendedModel,
  OffloadPreview,
  DownloadStatus,
  LlamaServerStatus,
  StartRequest,
  ChatRequest,
  ChatResponse,
  StreamChunk,
  ConversationSummary,
  ConversationDetail,
  SearchResult,
  ChatModels,
  LiteLLMStatus,
} from './types';

const API_BASE = '/api';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;

  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

export const api = {
  // ============ Status ============

  async health(): Promise<{ status: string }> {
    return request('/health');
  },

  async getStatus(): Promise<Status> {
    return request('/status');
  },

  async getHardware(): Promise<HardwareInfo> {
    return request('/hardware');
  },

  // ============ Models ============

  async getModels(refresh = false): Promise<{ models: LocalModel[]; count: number }> {
    return request(`/models${refresh ? '?refresh=true' : ''}`);
  },

  async scanModels(): Promise<{ models: LocalModel[]; count: number }> {
    return request('/models/scan', { method: 'POST' });
  },

  async getModelSources(): Promise<Record<string, { path: string; exists: boolean; model_count: number }>> {
    return request('/models/sources');
  },

  async getRecommendedModels(): Promise<{ models: RecommendedModel[] }> {
    return request('/models/recommended');
  },

  async getOffloadPreview(modelPath: string, contextSize = 4096): Promise<OffloadPreview> {
    return request('/models/offload-preview', {
      method: 'POST',
      body: JSON.stringify({ model_path: modelPath, context_size: contextSize }),
    });
  },

  // HuggingFace integration
  async searchHF(query: string, limit = 10): Promise<{ results: HFSearchResult[] }> {
    return request('/models/hf/search', {
      method: 'POST',
      body: JSON.stringify({ query, limit }),
    });
  },

  async listHFFiles(repoId: string): Promise<{ repo_id: string; files: HFModelFile[] }> {
    return request('/models/hf/files', {
      method: 'POST',
      body: JSON.stringify({ repo_id: repoId }),
    });
  },

  async parseHFUrl(url: string): Promise<{ repo_id: string; filename?: string }> {
    return request('/models/hf/parse', {
      method: 'POST',
      body: JSON.stringify({ url }),
    });
  },

  async downloadModel(repoId: string, filename: string): Promise<{ download_id: string; status: string }> {
    return request('/models/download', {
      method: 'POST',
      body: JSON.stringify({ repo_id: repoId, filename }),
    });
  },

  async getDownloads(): Promise<{ downloads: DownloadStatus[] }> {
    return request('/models/downloads');
  },

  // ============ Control ============

  async getServerStatus(): Promise<LlamaServerStatus> {
    return request('/control/status');
  },

  async startServer(req: StartRequest): Promise<{ status: string; model: string; gpu_layers: number; api_url: string }> {
    return request('/control/start', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  },

  async stopServer(): Promise<{ status: string }> {
    return request('/control/stop', { method: 'POST' });
  },

  async restartServer(): Promise<{ status: string; api_url: string }> {
    return request('/control/restart', { method: 'POST' });
  },

  async healthCheck(): Promise<{ healthy: boolean; api_url?: string; reason?: string }> {
    return request('/control/health');
  },

  async getMode(): Promise<{ mode: string; available_modes: string[] }> {
    return request('/control/mode');
  },

  async setMode(mode: string): Promise<{ mode: string; message: string }> {
    return request('/control/mode', {
      method: 'POST',
      body: JSON.stringify({ mode }),
    });
  },

  async getConfig(): Promise<{
    mode: string;
    context_size: number;
    gpu_layers?: number;
    host: string;
    port: number;
    litellm_enabled: boolean;
    models_dir: string;
  }> {
    return request('/control/config');
  },

  // Log streaming via SSE
  streamLogs(onMessage: (data: { type: string; data?: any }) => void): EventSource {
    const eventSource = new EventSource(`${API_BASE}/control/logs`);
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch {
        // Ignore parse errors
      }
    };
    return eventSource;
  },

  // ============ Chat ============

  async getChatModels(): Promise<ChatModels> {
    return request('/chat/models');
  },

  async chatCompletion(req: ChatRequest): Promise<ChatResponse> {
    return request('/chat/completions', {
      method: 'POST',
      body: JSON.stringify({ ...req, stream: false }),
    });
  },

  // Streaming chat completion
  async *streamChat(req: ChatRequest): AsyncGenerator<StreamChunk> {
    const response = await fetch(`${API_BASE}/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...req, stream: true }),
    });

    if (!response.ok) {
      throw new Error(`Chat error: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const chunk: StreamChunk = JSON.parse(line.slice(6));
            yield chunk;
            if (chunk.done || chunk.error) return;
          } catch {
            // Ignore parse errors
          }
        }
      }
    }
  },

  async abortChat(): Promise<{ status: string }> {
    return request('/chat/abort', { method: 'POST' });
  },

  // ============ Conversations ============

  async getConversations(limit = 50, offset = 0): Promise<ConversationSummary[]> {
    return request(`/conversations?limit=${limit}&offset=${offset}`);
  },

  async getConversationCount(): Promise<{ count: number }> {
    return request('/conversations/count');
  },

  async getConversation(id: string): Promise<ConversationDetail> {
    return request(`/conversations/${id}`);
  },

  async updateConversationTitle(id: string, title: string): Promise<{ status: string; title: string }> {
    return request(`/conversations/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ title }),
    });
  },

  async deleteConversation(id: string): Promise<{ status: string }> {
    return request(`/conversations/${id}`, { method: 'DELETE' });
  },

  async deleteAllConversations(): Promise<{ status: string }> {
    return request('/conversations', { method: 'DELETE' });
  },

  async searchConversations(query: string, limit = 20): Promise<SearchResult[]> {
    return request(`/conversations/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  },

  async exportConversationJSON(id: string): Promise<Blob> {
    const response = await fetch(`${API_BASE}/conversations/${id}/export/json`);
    if (!response.ok) throw new Error('Export failed');
    return response.blob();
  },

  async exportConversationMarkdown(id: string): Promise<Blob> {
    const response = await fetch(`${API_BASE}/conversations/${id}/export/markdown`);
    if (!response.ok) throw new Error('Export failed');
    return response.blob();
  },

  async importConversation(data: {
    title?: string;
    model?: string;
    messages: { role: string; content: string }[];
  }): Promise<{ status: string; conversation_id: string; message_count: number }> {
    return request('/conversations/import', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
};
