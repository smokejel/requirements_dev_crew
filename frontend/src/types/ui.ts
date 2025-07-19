// UI-specific types

export interface UploadedFile {
  file: File;
  id: string;
  progress: number;
  uploaded: boolean;
  error?: string;
}

export interface APIKeyState {
  openai: string;
  anthropic: string;
  google: string;
}

export interface APIKeyVisibility {
  openai: boolean;
  anthropic: boolean;
  google: boolean;
}

export interface AgentConfigState {
  requirements_analyst: {
    provider: string;
    model: string;
  };
  decomposition_strategist: {
    provider: string;
    model: string;
  };
  requirements_engineer: {
    provider: string;
    model: string;
  };
  quality_assurance: {
    provider: string;
    model: string;
  };
  documentation_specialist: {
    provider: string;
    model: string;
  };
}

export interface ModelOptions {
  openai: string[];
  anthropic: string[];
  google: string[];
}

export interface AgentDisplayNames {
  requirements_analyst: string;
  decomposition_strategist: string;
  requirements_engineer: string;
  quality_assurance: string;
  documentation_specialist: string;
}

export interface ExecutionResults {
  status: string;
  message: string;
  output?: string;
  error?: string;
  started_at?: string;
  completed_at?: string;
}

export interface TabType {
  id: string;
  name: string;
  active: boolean;
}

export interface NavigationState {
  activeTab: string;
  tabs: TabType[];
}