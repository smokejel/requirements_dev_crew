import React, { useState, useEffect, useCallback } from 'react';
import { Upload, Settings, Play, Download, Eye, EyeOff, Key, FileText, X, AlertCircle } from 'lucide-react';
import { APIProvider } from './types/apiTypes';
import type { AgentConfig, CrewExecutionStatus } from './types/apiTypes';
import { useAPI, useWebSocket, useFileUpload } from './hooks';

const App: React.FC = () => {
  const [apiKeys, setApiKeys] = useState({
    openai: '',
    google: '',
    anthropic: ''
  });
  
  const [showKeys, setShowKeys] = useState({
    openai: false,
    google: false,
    anthropic: false
  });
  
  const [agentConfigs, setAgentConfigs] = useState<Record<string, AgentConfig>>({
    requirements_analyst: { provider: APIProvider.OPENAI, model: 'gpt-4' },
    decomposition_strategist: { provider: APIProvider.OPENAI, model: 'gpt-4' },
    requirements_engineer: { provider: APIProvider.ANTHROPIC, model: 'claude-3-sonnet' },
    quality_assurance: { provider: APIProvider.OPENAI, model: 'gpt-4' },
    documentation_specialist: { provider: APIProvider.GOOGLE, model: 'gemini-pro' }
  });
  
  const [prompt, setPrompt] = useState('');
  const [currentExecution, setCurrentExecution] = useState<CrewExecutionStatus | null>(null);
  const [executionHistory, setExecutionHistory] = useState<CrewExecutionStatus[]>([]);

  // Hooks
  const api = useAPI();
  const ws = useWebSocket();
  const fileUpload = useFileUpload();

  const modelOptions = {
    [APIProvider.OPENAI]: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'],
    [APIProvider.ANTHROPIC]: ['claude-3-sonnet', 'claude-3-opus', 'claude-3-haiku'],
    [APIProvider.GOOGLE]: ['gemini-pro', 'gemini-pro-vision', 'gemini-1.5-pro']
  };

  const agentDisplayNames = {
    requirements_analyst: 'Requirements Analyst',
    decomposition_strategist: 'Decomposition Strategist', 
    requirements_engineer: 'Requirements Engineer',
    quality_assurance: 'Quality Assurance',
    documentation_specialist: 'Documentation Specialist'
  };

  // Load initial configuration
  useEffect(() => {
    const loadConfig = async () => {
      const config = await api.getConfiguration();
      if (config) {
        // Update agent configs from backend
        setAgentConfigs(config.agent_configs);
        
        // Set masked API keys
        setApiKeys(prev => ({
          ...prev,
          ...config.api_keys
        }));
      }
    };
    
    loadConfig();
  }, []);

  // Load execution history
  useEffect(() => {
    const loadHistory = async () => {
      const history = await api.getExecutionHistory();
      if (history) {
        setExecutionHistory(history);
      }
    };
    
    loadHistory();
  }, []);

  // Subscribe to execution updates via WebSocket
  useEffect(() => {
    if (currentExecution && ws.connected) {
      ws.subscribe(currentExecution.execution_id);
      
      return () => {
        ws.unsubscribe(currentExecution.execution_id);
      };
    }
  }, [currentExecution, ws.connected]);

  // Monitor execution updates
  useEffect(() => {
    if (currentExecution) {
      const latestUpdate = ws.getLatestExecutionUpdate(currentExecution.execution_id);
      if (latestUpdate && latestUpdate.type === 'completion') {
        // Execution completed, refresh status
        const refreshStatus = async () => {
          const status = await api.getExecutionStatus(currentExecution.execution_id);
          if (status) {
            setCurrentExecution(status);
          }
        };
        refreshStatus();
      }
    }
  }, [ws.executionUpdates, currentExecution]);

  const handleApiKeyChange = useCallback((provider: string, value: string) => {
    setApiKeys(prev => ({ ...prev, [provider]: value }));
  }, []);

  const handleApiKeyBlur = useCallback(async (provider: string) => {
    const key = apiKeys[provider as keyof typeof apiKeys];
    if (key && key.length > 10) {
      await api.setAPIKey(provider as APIProvider, key);
    }
  }, [apiKeys, api]);

  const toggleKeyVisibility = useCallback((provider: string) => {
    setShowKeys(prev => ({ ...prev, [provider]: !prev[provider as keyof typeof prev] }));
  }, []);

  const handleAgentConfigChange = useCallback(async (agent: string, field: string, value: string) => {
    const updatedConfig = { ...agentConfigs[agent], [field]: value };
    setAgentConfigs(prev => ({ ...prev, [agent]: updatedConfig }));
    
    // Update backend
    await api.updateAgentConfig(agent, updatedConfig);
  }, [agentConfigs, api]);

  const handleFileUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    fileUpload.addFiles(files);
  }, [fileUpload]);

  const handleRunDecomposition = useCallback(async () => {
    if (!prompt.trim()) return;
    
    // First upload any remaining files
    let fileIds: string[] = [];
    if (!fileUpload.allUploaded() && fileUpload.files.length > 0) {
      const responses = await fileUpload.uploadAllFiles();
      fileIds = responses?.map(r => r.file_id) || [];
    } else {
      fileIds = fileUpload.getUploadedFileIds();
    }

    // Setup API keys
    const filteredKeys = Object.entries(apiKeys)
      .filter(([_, key]) => key.trim() !== '')
      .reduce((acc, [provider, key]) => ({ ...acc, [provider]: key }), {});
    
    if (Object.keys(filteredKeys).length > 0) {
      await api.setupAPIKeys(filteredKeys);
    }

    // Execute crew
    const execution = await api.executeCrew({
      prompt,
      uploaded_files: fileIds,
      agent_configs: agentConfigs,
      execution_mode: 'run'
    });

    if (execution) {
      const status = await api.getExecutionStatus(execution.execution_id);
      if (status) {
        setCurrentExecution(status);
      }
    }
  }, [prompt, fileUpload, apiKeys, agentConfigs, api]);

  const handleCancelExecution = useCallback(() => {
    if (currentExecution) {
      ws.cancelExecution(currentExecution.execution_id);
    }
  }, [currentExecution, ws]);

  const handleDownloadResults = useCallback(async () => {
    if (currentExecution) {
      const blob = await api.downloadResults(currentExecution.execution_id);
      if (blob) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `results-${currentExecution.execution_id}.md`;
        a.click();
        URL.revokeObjectURL(url);
      }
    }
  }, [currentExecution, api]);

  const isRunning = currentExecution?.status === 'running' || currentExecution?.status === 'pending';
  const canRun = !isRunning && prompt.trim().length > 0 && (fileUpload.files.length > 0 || fileUpload.allUploaded());

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-gray-100">
      {/* Header/Navigation */}
      <header className="bg-gray-800 border-b border-gray-700 shadow-sm">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo and Title */}
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 bg-orange-600 rounded-lg flex items-center justify-center">
                <Settings className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-100">CrewAI Requirements Decomposer</h1>
                <p className="text-sm text-gray-400">Intelligent System Requirements Analysis</p>
              </div>
            </div>

            {/* Connection Status */}
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className={`h-2 w-2 rounded-full ${ws.connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-sm text-gray-400">
                  {ws.connected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              
              <nav className="flex items-center gap-6">
                <button className="text-orange-400 font-medium border-b-2 border-orange-400 pb-1">
                  Decomposition
                </button>
                <button className="text-gray-400 hover:text-gray-200 font-medium pb-1">
                  History ({executionHistory.length})
                </button>
              </nav>
            </div>
          </div>
        </div>
      </header>

      {/* Error Display */}
      {api.error && (
        <div className="bg-red-900 border-l-4 border-red-500 p-4 mx-6 mt-4">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-400 mr-3" />
            <span className="text-red-200">{api.error}</span>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel - Configuration */}
        <div className="w-1/3 bg-gray-800 border-r border-gray-700 overflow-y-auto">
          <div className="p-6">
            <div className="flex items-center gap-2 mb-6">
              <Settings className="h-6 w-6 text-orange-400" />
              <h2 className="text-xl font-semibold text-gray-100">Configuration</h2>
            </div>

            {/* API Keys Section */}
            <div className="mb-8">
              <h3 className="text-lg font-medium text-gray-200 mb-4 flex items-center gap-2">
                <Key className="h-5 w-5" />
                API Keys
              </h3>
              
              {Object.entries(apiKeys).map(([provider, key]) => (
                <div key={provider} className="mb-4">
                  <label className="block text-sm font-medium text-gray-300 mb-2 capitalize">
                    {provider} API Key
                  </label>
                  <div className="relative">
                    <input
                      type={showKeys[provider as keyof typeof showKeys] ? 'text' : 'password'}
                      value={key}
                      onChange={(e) => handleApiKeyChange(provider, e.target.value)}
                      onBlur={() => handleApiKeyBlur(provider)}
                      className="w-full px-3 py-2 pr-10 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent text-gray-100 placeholder-gray-400"
                      placeholder={`Enter ${provider} API key`}
                    />
                    <button
                      type="button"
                      onClick={() => toggleKeyVisibility(provider)}
                      className="absolute right-3 top-2.5 text-gray-400 hover:text-gray-200"
                    >
                      {showKeys[provider as keyof typeof showKeys] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Agent Model Configuration */}
            <div className="mb-8">
              <h3 className="text-lg font-medium text-gray-200 mb-4">Agent Model Configuration</h3>
              
              {Object.entries(agentConfigs).map(([agent, config]) => (
                <div key={agent} className="mb-6 p-4 bg-gray-700 rounded-lg border border-gray-600">
                  <h4 className="font-medium text-gray-100 mb-3">{agentDisplayNames[agent as keyof typeof agentDisplayNames]}</h4>
                  
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">Provider</label>
                      <select
                        value={config.provider}
                        onChange={(e) => handleAgentConfigChange(agent, 'provider', e.target.value)}
                        className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded focus:outline-none focus:ring-2 focus:ring-orange-500 text-gray-100"
                      >
                        <option value={APIProvider.OPENAI}>OpenAI</option>
                        <option value={APIProvider.ANTHROPIC}>Anthropic</option>
                        <option value={APIProvider.GOOGLE}>Google</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">Model</label>
                      <select
                        value={config.model}
                        onChange={(e) => handleAgentConfigChange(agent, 'model', e.target.value)}
                        className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded focus:outline-none focus:ring-2 focus:ring-orange-500 text-gray-100"
                      >
                        {modelOptions[config.provider]?.map(model => (
                          <option key={model} value={model}>{model}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Center Panel - Document Upload and Prompt */}
        <div className="flex-1 flex flex-col overflow-y-auto">
          
          {/* Document Upload Section */}
          <div className="bg-gray-800 border-b border-gray-700 p-6">
            <h3 className="text-lg font-medium text-gray-200 mb-4 flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Document Upload
            </h3>
            
            <div className="border-2 border-dashed border-gray-600 rounded-lg p-6 text-center hover:bg-gray-700 hover:border-gray-500 transition-colors">
              <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <div className="mb-4">
                <label htmlFor="file-upload" className="cursor-pointer">
                  <span className="text-orange-400 hover:text-orange-300 font-medium">Upload documents</span>
                  <span className="text-gray-400"> or drag and drop</span>
                </label>
                <input
                  id="file-upload"
                  type="file"
                  multiple
                  accept=".pdf,.doc,.docx,.txt,.md"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </div>
              <p className="text-sm text-gray-400">PDF, DOC, DOCX, TXT, MD up to 10MB each</p>
            </div>

            {/* Uploaded Files List */}
            {fileUpload.files.length > 0 && (
              <div className="mt-4">
                <h4 className="text-sm font-medium text-gray-300 mb-2">Files:</h4>
                <div className="space-y-2">
                  {fileUpload.files.map((file, index) => (
                    <div key={index} className="flex items-center justify-between bg-gray-700 px-3 py-2 rounded border border-gray-600">
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-200">{file.file.name}</span>
                        {file.uploading && <div className="animate-spin h-4 w-4 border-2 border-orange-500 border-t-transparent rounded-full"></div>}
                        {file.uploaded && <div className="h-2 w-2 bg-green-500 rounded-full"></div>}
                        {file.error && <AlertCircle className="h-4 w-4 text-red-400" />}
                      </div>
                      <button
                        onClick={() => fileUpload.removeFile(index)}
                        className="text-red-400 hover:text-red-300"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Prompt Section */}
          <div className="flex-1 bg-gray-900 p-6 pb-8">
            <h3 className="text-lg font-medium text-gray-200 mb-4">Requirements Decomposition Prompt</h3>
            
            <div className="flex flex-col h-full">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Enter your requirements decomposition instructions here. For example: 'Decompose the uploaded system requirements document into subsystem-level requirements for the Emergency Communication System. Focus on functional requirements allocation and interface definitions.'"
                className="flex-1 w-full p-4 bg-gray-800 border border-gray-600 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent text-gray-100 placeholder-gray-400"
                rows={8}
              />
              
              <div className="flex items-center justify-between mt-4">
                <div className="text-sm text-gray-400">
                  {fileUpload.files.length} file(s) • {prompt.length} characters
                </div>
                
                <div className="flex items-center gap-2">
                  {isRunning && (
                    <button
                      onClick={handleCancelExecution}
                      className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                    >
                      Cancel
                    </button>
                  )}
                  
                  <button
                    onClick={handleRunDecomposition}
                    disabled={!canRun || api.loading}
                    className="flex items-center gap-2 px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors"
                  >
                    {api.loading || isRunning ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                        {isRunning ? 'Running...' : 'Starting...'}
                      </>
                    ) : (
                      <>
                        <Play className="h-4 w-4" />
                        Run Decomposition
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Results Section */}
          {currentExecution && (
            <div className="bg-gray-800 border-t border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-200">Results</h3>
                {currentExecution.status === 'completed' && (
                  <button 
                    onClick={handleDownloadResults}
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                  >
                    <Download className="h-4 w-4" />
                    Download Results
                  </button>
                )}
              </div>
              
              <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                <div className="flex items-center gap-2 mb-3">
                  <div className={`h-3 w-3 rounded-full ${
                    currentExecution.status === 'completed' ? 'bg-green-500' :
                    currentExecution.status === 'failed' ? 'bg-red-500' :
                    'bg-orange-500'
                  }`}></div>
                  <span className="font-medium text-gray-200">{currentExecution.status.toUpperCase()}</span>
                  <span className="text-sm text-gray-400">
                    {Math.round(currentExecution.progress * 100)}%
                  </span>
                </div>
                
                {currentExecution.current_agent && (
                  <p className="text-sm text-gray-300 mb-2">
                    Current Agent: {currentExecution.current_agent}
                  </p>
                )}
                
                {currentExecution.output && (
                  <div className="bg-gray-800 p-3 rounded border border-gray-600 mt-3">
                    <pre className="text-sm text-gray-300 whitespace-pre-wrap">{currentExecution.output}</pre>
                  </div>
                )}
                
                {currentExecution.error && (
                  <div className="bg-red-900 p-3 rounded border border-red-600 mt-3">
                    <p className="text-sm text-red-200">{currentExecution.error}</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default App;