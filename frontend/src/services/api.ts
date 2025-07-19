import axios from 'axios';
import type { AxiosInstance } from 'axios';
import { APIProvider } from '../types/apiTypes';
import type {
  APIKeyRequest,
  APIKeyResponse,
  AgentConfig,
  CrewExecutionRequest,
  CrewExecutionResponse,
  CrewExecutionStatus,
  FileUploadResponse,
  FileInfo,
  ConfigurationResponse,
  HealthResponse
} from '../types/apiTypes';

class APIClient {
  private client: AxiosInstance;

  constructor(baseURL: string = '') {
    this.client = axios.create({
      baseURL: `${baseURL}/api`,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error);
        return Promise.reject(error);
      }
    );
  }

  // Health check
  async healthCheck(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health');
    return response.data;
  }

  // Configuration endpoints
  async getConfiguration(): Promise<ConfigurationResponse> {
    const response = await this.client.get<ConfigurationResponse>('/config/');
    return response.data;
  }

  async getAgentConfigs(): Promise<Record<string, AgentConfig>> {
    const response = await this.client.get<Record<string, AgentConfig>>('/config/agents');
    return response.data;
  }

  async updateAgentConfig(agentName: string, config: AgentConfig): Promise<void> {
    await this.client.put(`/config/agents/${agentName}`, config);
  }

  // API Key management
  async setAPIKey(request: APIKeyRequest): Promise<APIKeyResponse> {
    const response = await this.client.post<APIKeyResponse>('/auth/api-key', request);
    return response.data;
  }

  async getAPIKeys(): Promise<Record<APIProvider, string>> {
    const response = await this.client.get<Record<APIProvider, string>>('/auth/api-keys');
    return response.data;
  }

  async deleteAPIKey(provider: APIProvider): Promise<void> {
    await this.client.delete(`/auth/api-key/${provider}`);
  }

  // File operations
  async uploadFile(file: File): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post<FileUploadResponse>('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async getFiles(): Promise<FileInfo[]> {
    const response = await this.client.get<FileInfo[]>('/files');
    return response.data;
  }

  async getFileInfo(fileId: string): Promise<FileInfo> {
    const response = await this.client.get<FileInfo>(`/files/${fileId}`);
    return response.data;
  }

  async deleteFile(fileId: string): Promise<void> {
    await this.client.delete(`/files/${fileId}`);
  }

  async processFile(fileId: string): Promise<FileInfo> {
    const response = await this.client.post<FileInfo>(`/files/${fileId}/process`);
    return response.data;
  }

  async previewFile(fileId: string): Promise<FileInfo> {
    const response = await this.client.get<FileInfo>(`/files/${fileId}/preview`);
    return response.data;
  }

  // Crew execution
  async executeCrew(request: CrewExecutionRequest): Promise<CrewExecutionResponse> {
    const response = await this.client.post<CrewExecutionResponse>('/crew/execute', request);
    return response.data;
  }

  async getExecutionStatus(executionId: string): Promise<CrewExecutionStatus> {
    const response = await this.client.get<CrewExecutionStatus>(`/crew/execution/${executionId}`);
    return response.data;
  }

  async getExecutionHistory(): Promise<CrewExecutionStatus[]> {
    const response = await this.client.get<CrewExecutionStatus[]>('/crew/executions');
    return response.data;
  }

  async cancelExecution(executionId: string): Promise<void> {
    await this.client.post(`/crew/execution/${executionId}/cancel`);
  }

  async downloadResults(executionId: string): Promise<Blob> {
    const response = await this.client.get(`/crew/execution/${executionId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  }

  // WebSocket info
  async getWebSocketInfo(): Promise<any> {
    const response = await this.client.get('/ws/info');
    return response.data;
  }

  // Utility methods
  async uploadFiles(files: File[]): Promise<FileUploadResponse[]> {
    const uploadPromises = files.map(file => this.uploadFile(file));
    return Promise.all(uploadPromises);
  }

  async setupAPIKeys(apiKeys: Record<string, string>): Promise<void> {
    const requests = Object.entries(apiKeys)
      .filter(([_, key]) => key.trim() !== '')
      .map(([provider, key]) => 
        this.setAPIKey({
          provider: provider as APIProvider,
          api_key: key
        })
      );
    
    await Promise.all(requests);
  }

  async waitForExecution(executionId: string, timeout: number = 30000): Promise<CrewExecutionStatus> {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      const status = await this.getExecutionStatus(executionId);
      
      if (status.status === 'completed' || status.status === 'failed' || status.status === 'cancelled') {
        return status;
      }
      
      // Wait 1 second before checking again
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    throw new Error(`Execution ${executionId} timed out after ${timeout}ms`);
  }
}

// Create singleton instance
export const apiClient = new APIClient();
export default APIClient;