from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum

class APIProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"

class APIKeyRequest(BaseModel):
    provider: APIProvider
    api_key: str = Field(..., min_length=10, description="API key for the provider")

class APIKeyResponse(BaseModel):
    provider: APIProvider
    is_valid: bool
    masked_key: str = Field(..., description="Masked API key for display")

class AgentConfig(BaseModel):
    provider: APIProvider
    model: str
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4000, ge=100, le=8000)

class AgentConfigRequest(BaseModel):
    agent_name: str
    config: AgentConfig

class CrewConfigRequest(BaseModel):
    agent_configs: Dict[str, AgentConfig]
    api_keys: Dict[APIProvider, str]

class CrewExecutionRequest(BaseModel):
    prompt: str = Field(..., min_length=10, description="Requirements decomposition prompt")
    uploaded_files: List[str] = Field(default=[], description="List of uploaded file IDs")
    agent_configs: Dict[str, AgentConfig]
    execution_mode: str = Field(default="run", description="Execution mode: run, train, test")

class CrewExecutionResponse(BaseModel):
    execution_id: str
    status: str
    message: str
    started_at: str

class CrewExecutionStatus(BaseModel):
    execution_id: str
    status: str  # pending, running, completed, failed
    progress: float = Field(ge=0.0, le=1.0)
    current_agent: Optional[str] = None
    current_task: Optional[str] = None
    output: Optional[str] = None
    error: Optional[str] = None
    completed_at: Optional[str] = None

class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    size: int
    content_type: str
    uploaded_at: str

class FileInfo(BaseModel):
    file_id: str
    filename: str
    size: int
    content_type: str
    uploaded_at: str
    processed: bool = False
    text_content: Optional[str] = None

class ConfigurationResponse(BaseModel):
    api_keys: Dict[APIProvider, str]  # Masked keys
    agent_configs: Dict[str, AgentConfig]
    default_settings: Dict[str, Any]

class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: str

class ErrorResponse(BaseModel):
    error: str
    detail: str
    timestamp: str