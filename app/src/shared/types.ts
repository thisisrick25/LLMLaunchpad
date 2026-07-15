/**
 * Shared TypeScript types for LLMLaunchpad.
 */

// Hardware types
export interface GPUInfo {
  name: string;
  memory_total_gb: number;
  memory_free_gb: number;
}

export interface HardwareInfo {
  cpu_count: number;
  cpu_name: string;
  ram_total_gb: number;
  ram_available_gb: number;
  platform: string;
  has_gpu: boolean;
  total_vram_gb: number;
  gpus: GPUInfo[];
}

// Service types
export interface ServiceStatus {
  running: boolean;
  model?: string | null;
}

export interface ServicesStatus {
  llama: ServiceStatus;
  litellm: ServiceStatus;
}

export interface ConfigStatus {
  mode: string;
  models_dir: string;
  context_size: number;
}

export interface Status {
  status: string;
  version: string;
  services: ServicesStatus;
  hardware: HardwareInfo;
  config: ConfigStatus;
}

// Model types
export interface LocalModel {
  name: string;
  path: string;
  size_bytes: number;
  source: string;
  quantization?: string;
  family?: string;
  size_gb?: number;
}

export interface HFModelFile {
  filename: string;
  size_bytes: number;
}

export interface HFSearchResult {
  repo_id: string;
  downloads: number;
  last_modified: string;
}

export interface RecommendedModel {
  repo_id: string;
  name: string;
  description: string;
  sizes: string[];
  family: string;
}

export interface OffloadRecommendation {
  gpu_layers: number;
  total_layers: number;
  estimated_vram_mb: number;
  mode: string;
  reason: string;
}

export interface OffloadPreview {
  model_path: string;
  model_size_gb: number;
  context_size: number;
  recommendations: Record<string, OffloadRecommendation>;
  hardware: {
    has_gpu: boolean;
    total_vram_gb: number;
    gpus: { name: string; total_gb: number; free_gb: number }[];
  };
}

export interface DownloadStatus {
  status: 'starting' | 'downloading' | 'completed' | 'error';
  repo_id: string;
  filename: string;
  progress: number;
  error?: string;
  local_path?: string;
}

// Control types
export interface LlamaServerStatus {
  state: 'stopped' | 'starting' | 'running' | 'stopping' | 'error';
  model_path?: string;
  model_name?: string;
  host?: string;
  port?: number;
  gpu_layers: number;
  pid?: number;
  error?: string;
  api_url?: string;
}

export interface StartRequest {
  model: string;
  mode?: string;
  context_size?: number;
  gpu_layers?: number;
  port?: number;
}

// Chat types
export interface ChatMessage {
  id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at?: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  conversation_id?: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
}

export interface ChatResponse {
  id: string;
  conversation_id: string;
  content: string;
  model: string;
  finish_reason: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface StreamChunk {
  content?: string;
  conversation_id?: string;
  done?: boolean;
  aborted?: boolean;
  error?: string;
}

// Conversation types
export interface ConversationSummary {
  id: string;
  title: string;
  model?: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ConversationDetail {
  id: string;
  title: string;
  model?: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
}

export interface SearchResult {
  conversation_id: string;
  conversation_title: string;
  message_id: string;
  content: string;
  role: string;
  created_at: string;
}

// Cloud model types
export interface CloudModel {
  provider: string;
  model_id: string;
  display_name: string;
  context_length: number;
  input_cost_per_1k: number;
  output_cost_per_1k: number;
}

export interface ChatModels {
  local: {
    available: boolean;
    current_model?: string;
  };
  cloud: {
    available: boolean;
    models: CloudModel[];
  };
}

// LiteLLM types
export interface LiteLLMStatus {
  enabled: boolean;
  available: boolean;
  configured_providers: string[];
  cloud_models: CloudModel[];
}
