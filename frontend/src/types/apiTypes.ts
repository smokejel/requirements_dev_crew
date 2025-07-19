// API Types matching backend schemas.py

export const APIProvider = {
  OPENAI: "openai",
  ANTHROPIC: "anthropic",
  GOOGLE: "google"
} as const;

export type APIProvider = typeof APIProvider[keyof typeof APIProvider];

export interface APIKeyRequest {
  provider: APIProvider;
  api_key: string;
}

export interface APIKeyResponse {
  provider: APIProvider;
  is_valid: boolean;
  masked_key: string;
}

export interface AgentConfig {
  provider: APIProvider;
  model: string;
  temperature?: number;
  max_tokens?: number;
}

export interface AgentConfigRequest {
  agent_name: string;
  config: AgentConfig;
}

export interface CrewConfigRequest {
  agent_configs: Record<string, AgentConfig>;
  api_keys: Record<APIProvider, string>;
}

export interface CrewExecutionRequest {
  prompt: string;
  uploaded_files?: string[];
  agent_configs: Record<string, AgentConfig>;
  execution_mode?: string;
}

export interface CrewExecutionResponse {
  execution_id: string;
  status: string;
  message: string;
  started_at: string;
}

export interface CrewExecutionStatus {
  execution_id: string;
  status: string; // pending, running, completed, failed
  progress: number;
  current_agent?: string;
  current_task?: string;
  output?: string;
  error?: string;
  completed_at?: string;
}

export interface FileUploadResponse {
  file_id: string;
  filename: string;
  size: number;
  content_type: string;
  uploaded_at: string;
}

export interface FileInfo {
  file_id: string;
  filename: string;
  size: number;
  content_type: string;
  uploaded_at: string;
  processed?: boolean;
  text_content?: string;
}

export interface ConfigurationResponse {
  api_keys: Record<APIProvider, string>; // Masked keys
  agent_configs: Record<string, AgentConfig>;
  default_settings: Record<string, any>;
}

export interface HealthResponse {
  status: string;
  message: string;
  timestamp: string;
}

export interface ErrorResponse {
  error: string;
  detail: string;
  timestamp: string;
}

// WebSocket message types
export interface WebSocketMessage {
  type: string;
  execution_id?: string;
  data?: any;
  timestamp?: string;
  error?: string;
}

export interface ExecutionUpdate {
  type: string;
  execution_id: string;
  status: string;
  progress: number;
  current_agent?: string;
  current_task?: string;
  output?: string;
  error?: string;
}