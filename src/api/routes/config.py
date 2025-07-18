from fastapi import APIRouter, HTTPException, Depends
from ..models.schemas import AgentConfig, AgentConfigRequest, ConfigurationResponse
from ..services.config_service import ConfigService
from typing import Dict

router = APIRouter()

# Dependency to get config service
def get_config_service():
    return ConfigService()

@router.get("/agents", response_model=Dict[str, AgentConfig])
async def get_agent_configs(
    config_service: ConfigService = Depends(get_config_service)
):
    """Get all agent configurations"""
    return config_service.get_all_agent_configs()

@router.get("/agents/{agent_name}", response_model=AgentConfig)
async def get_agent_config(
    agent_name: str,
    config_service: ConfigService = Depends(get_config_service)
):
    """Get configuration for a specific agent"""
    config = config_service.get_agent_config(agent_name)
    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Agent configuration not found for {agent_name}"
        )
    
    return config

@router.post("/agents/{agent_name}")
async def store_agent_config(
    agent_name: str,
    config: AgentConfig,
    config_service: ConfigService = Depends(get_config_service)
):
    """Store configuration for an agent"""
    success = config_service.store_agent_config(agent_name, config)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to store agent configuration"
        )
    
    return {"message": f"Agent configuration for {agent_name} stored successfully"}

@router.get("/", response_model=ConfigurationResponse)
async def get_full_configuration(
    config_service: ConfigService = Depends(get_config_service)
):
    """Get full configuration (API keys masked and agent configs)"""
    return ConfigurationResponse(
        api_keys=config_service.get_all_api_keys_masked(),
        agent_configs=config_service.get_all_agent_configs(),
        default_settings={
            "max_file_size": 10 * 1024 * 1024,  # 10MB
            "supported_file_types": [".pdf", ".doc", ".docx", ".txt", ".md"],
            "max_files": 10,
            "execution_timeout": 300  # 5 minutes
        }
    )

@router.get("/model-options")
async def get_model_options():
    """Get available model options for each provider"""
    return {
        "openai": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"],
        "anthropic": ["claude-3-sonnet-20240229", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
        "google": ["gemini-pro", "gemini-pro-vision", "gemini-1.5-pro"]
    }

@router.get("/agent-types")
async def get_agent_types():
    """Get available agent types and their display names"""
    return {
        "requirements_analyst": "Requirements Analyst",
        "decomposition_strategist": "Decomposition Strategist",
        "requirements_engineer": "Requirements Engineer",
        "quality_assurance_agent": "Quality Assurance",
        "documentation_specialist": "Documentation Specialist"
    }