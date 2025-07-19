import { useState, useCallback } from 'react';
import { apiClient } from '../services/api';
import { APIProvider } from '../types/apiTypes';
import type { AgentConfig, CrewExecutionRequest } from '../types/apiTypes';

export const useAPI = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAsync = useCallback(async <T>(asyncFn: () => Promise<T>): Promise<T | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await asyncFn();
      return result;
    } catch (err: any) {
      const errorMessage = err.response?.data?.error || err.message || 'An error occurred';
      setError(errorMessage);
      console.error('API Error:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const healthCheck = useCallback(() => {
    return handleAsync(() => apiClient.healthCheck());
  }, [handleAsync]);

  const uploadFile = useCallback((file: File) => {
    return handleAsync(() => apiClient.uploadFile(file));
  }, [handleAsync]);

  const uploadFiles = useCallback((files: File[]) => {
    return handleAsync(() => apiClient.uploadFiles(files));
  }, [handleAsync]);

  const setAPIKey = useCallback((provider: APIProvider, apiKey: string) => {
    return handleAsync(() => apiClient.setAPIKey({ provider, api_key: apiKey }));
  }, [handleAsync]);

  const setupAPIKeys = useCallback((apiKeys: Record<string, string>) => {
    return handleAsync(() => apiClient.setupAPIKeys(apiKeys));
  }, [handleAsync]);

  const updateAgentConfig = useCallback((agentName: string, config: AgentConfig) => {
    return handleAsync(() => apiClient.updateAgentConfig(agentName, config));
  }, [handleAsync]);

  const executeCrew = useCallback((request: CrewExecutionRequest) => {
    return handleAsync(() => apiClient.executeCrew(request));
  }, [handleAsync]);

  const getExecutionStatus = useCallback((executionId: string) => {
    return handleAsync(() => apiClient.getExecutionStatus(executionId));
  }, [handleAsync]);

  const cancelExecution = useCallback((executionId: string) => {
    return handleAsync(() => apiClient.cancelExecution(executionId));
  }, [handleAsync]);

  const downloadResults = useCallback((executionId: string) => {
    return handleAsync(() => apiClient.downloadResults(executionId));
  }, [handleAsync]);

  const getFiles = useCallback(() => {
    return handleAsync(() => apiClient.getFiles());
  }, [handleAsync]);

  const deleteFile = useCallback((fileId: string) => {
    return handleAsync(() => apiClient.deleteFile(fileId));
  }, [handleAsync]);

  const getConfiguration = useCallback(() => {
    return handleAsync(() => apiClient.getConfiguration());
  }, [handleAsync]);

  const getExecutionHistory = useCallback(() => {
    return handleAsync(() => apiClient.getExecutionHistory());
  }, [handleAsync]);

  return {
    loading,
    error,
    healthCheck,
    uploadFile,
    uploadFiles,
    setAPIKey,
    setupAPIKeys,
    updateAgentConfig,
    executeCrew,
    getExecutionStatus,
    cancelExecution,
    downloadResults,
    getFiles,
    deleteFile,
    getConfiguration,
    getExecutionHistory,
  };
};

export default useAPI;