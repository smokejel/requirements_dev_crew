import React, { useState } from 'react';
import { Upload, Settings, Play, Download, Eye, EyeOff, Key, FileText, Send, X } from 'lucide-react';

const CrewAIRequirementsUI = () => {
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
  
  const [agentConfigs, setAgentConfigs] = useState({
    requirements_analyst: { provider: 'openai', model: 'gpt-4' },
    decomposition_strategist: { provider: 'openai', model: 'gpt-4' },
    requirements_engineer: { provider: 'anthropic', model: 'claude-3-sonnet' },
    quality_assurance: { provider: 'openai', model: 'gpt-4' },
    documentation_specialist: { provider: 'google', model: 'gemini-pro' }
  });
  
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [prompt, setPrompt] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [results, setResults] = useState(null);

  const modelOptions = {
    openai: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'],
    anthropic: ['claude-3-sonnet', 'claude-3-opus', 'claude-3-haiku'],
    google: ['gemini-pro', 'gemini-pro-vision', 'gemini-1.5-pro']
  };

  const agentDisplayNames = {
    requirements_analyst: 'Requirements Analyst',
    decomposition_strategist: 'Decomposition Strategist', 
    requirements_engineer: 'Requirements Engineer',
    quality_assurance: 'Quality Assurance',
    documentation_specialist: 'Documentation Specialist'
  };

  const handleApiKeyChange = (provider, value) => {
    setApiKeys(prev => ({ ...prev, [provider]: value }));
  };

  const toggleKeyVisibility = (provider) => {
    setShowKeys(prev => ({ ...prev, [provider]: !prev[provider] }));
  };

  const handleAgentConfigChange = (agent, field, value) => {
    setAgentConfigs(prev => ({
      ...prev,
      [agent]: { ...prev[agent], [field]: value }
    }));
  };

  const handleFileUpload = (event) => {
    const files = Array.from(event.target.files);
    setUploadedFiles(prev => [...prev, ...files]);
  };

  const removeFile = (index) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleRunDecomposition = async () => {
    setIsRunning(true);
    // Simulate processing
    setTimeout(() => {
      setResults({
        status: 'completed',
        message: 'Requirements decomposition completed successfully',
        output: 'Sample decomposition results would appear here...'
      });
      setIsRunning(false);
    }, 3000);
  };

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

            {/* Navigation Menu */}
            <nav className="flex items-center gap-6">
              <button className="text-orange-400 font-medium border-b-2 border-orange-400 pb-1">
                Decomposition
              </button>
              <button className="text-gray-400 hover:text-gray-200 font-medium pb-1">
                History
              </button>
              <button className="text-gray-400 hover:text-gray-200 font-medium pb-1">
                Templates
              </button>
              <button className="text-gray-400 hover:text-gray-200 font-medium pb-1">
                Reports
              </button>
            </nav>

            {/* User Actions */}
            <div className="flex items-center gap-3">
              <button className="text-gray-400 hover:text-gray-200">
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5v-5z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 21H7a2 2 0 01-2-2V5a2 2 0 012-2h10a2 2 0 012 2v16z" />
                </svg>
              </button>
              <button className="text-gray-400 hover:text-gray-200">
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </button>
              <div className="h-8 w-8 bg-gray-600 rounded-full flex items-center justify-center">
                <span className="text-sm font-medium text-gray-200">MS</span>
              </div>
            </div>
          </div>
        </div>
      </header>

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
                      type={showKeys[provider] ? 'text' : 'password'}
                      value={key}
                      onChange={(e) => handleApiKeyChange(provider, e.target.value)}
                      className="w-full px-3 py-2 pr-10 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent text-gray-100 placeholder-gray-400"
                      placeholder={`Enter ${provider} API key`}
                    />
                    <button
                      type="button"
                      onClick={() => toggleKeyVisibility(provider)}
                      className="absolute right-3 top-2.5 text-gray-400 hover:text-gray-200"
                    >
                      {showKeys[provider] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
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
                  <h4 className="font-medium text-gray-100 mb-3">{agentDisplayNames[agent]}</h4>
                  
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">Provider</label>
                      <select
                        value={config.provider}
                        onChange={(e) => handleAgentConfigChange(agent, 'provider', e.target.value)}
                        className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded focus:outline-none focus:ring-2 focus:ring-orange-500 text-gray-100"
                      >
                        <option value="openai">OpenAI</option>
                        <option value="anthropic">Anthropic</option>
                        <option value="google">Google</option>
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
        <div className="flex-1 flex flex-col">
          
          {/* Document Upload Section */}
          <div className="bg-gray-800 border-b border-gray-700 p-6">
            <h3 className="text-lg font-medium text-gray-200 mb-4 flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Document Upload
            </h3>
            
            <div className="border-2 border-dashed border-gray-600 rounded-lg p-6 text-center bg-gray-750 hover:bg-gray-700 hover:border-gray-500 transition-colors">
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
            {uploadedFiles.length > 0 && (
              <div className="mt-4">
                <h4 className="text-sm font-medium text-gray-300 mb-2">Uploaded Files:</h4>
                <div className="space-y-2">
                  {uploadedFiles.map((file, index) => (
                    <div key={index} className="flex items-center justify-between bg-gray-700 px-3 py-2 rounded border border-gray-600">
                      <span className="text-sm text-gray-200">{file.name}</span>
                      <button
                        onClick={() => removeFile(index)}
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
          <div className="flex-1 bg-gray-900 p-6">
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
                  {uploadedFiles.length} file(s) uploaded • {prompt.length} characters
                </div>
                
                <button
                  onClick={handleRunDecomposition}
                  disabled={isRunning || !prompt.trim() || uploadedFiles.length === 0}
                  className="flex items-center gap-2 px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors"
                >
                  {isRunning ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                      Processing...
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

          {/* Results Section */}
          {(results || isRunning) && (
            <div className="bg-gray-800 border-t border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-200">Results</h3>
                {results && (
                  <button className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors">
                    <Download className="h-4 w-4" />
                    Download Results
                  </button>
                )}
              </div>
              
              {isRunning ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-12 w-12 border-4 border-orange-600 border-t-transparent mx-auto mb-4"></div>
                  <p className="text-gray-300">Processing requirements decomposition...</p>
                  <p className="text-sm text-gray-400 mt-2">This may take a few minutes</p>
                </div>
              ) : results ? (
                <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="h-3 w-3 bg-green-500 rounded-full"></div>
                    <span className="font-medium text-green-400">{results.status.toUpperCase()}</span>
                  </div>
                  <p className="text-gray-200 mb-3">{results.message}</p>
                  <div className="bg-gray-800 p-3 rounded border border-gray-600">
                    <pre className="text-sm text-gray-300 whitespace-pre-wrap">{results.output}</pre>
                  </div>
                </div>
              ) : null}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CrewAIRequirementsUI;