from fastapi import APIRouter, HTTPException, Depends
from ..models.schemas import APIKeyRequest, APIKeyResponse, APIProvider
from ..services.config_service import ConfigService
from typing import Dict

router = APIRouter()

# Dependency to get config service
def get_config_service():
    return ConfigService()

@router.post("/api-keys", response_model=APIKeyResponse)
async def store_api_key(
    request: APIKeyRequest,
    config_service: ConfigService = Depends(get_config_service)
):
    """Store API key for a provider"""
    # Validate API key format
    if not config_service.validate_api_key(request.provider, request.api_key):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid API key format for {request.provider}"
        )
    
    # Store API key
    success = config_service.store_api_key(request.provider, request.api_key)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to store API key"
        )
    
    return APIKeyResponse(
        provider=request.provider,
        is_valid=True,
        masked_key=config_service.get_masked_api_key(request.provider)
    )

@router.get("/api-keys", response_model=Dict[str, str])
async def get_api_keys(
    config_service: ConfigService = Depends(get_config_service)
):
    """Get all API keys (masked)"""
    return config_service.get_all_api_keys_masked()

@router.get("/api-keys/{provider}", response_model=APIKeyResponse)
async def get_api_key(
    provider: APIProvider,
    config_service: ConfigService = Depends(get_config_service)
):
    """Get API key for a specific provider (masked)"""
    masked_key = config_service.get_masked_api_key(provider)
    
    return APIKeyResponse(
        provider=provider,
        is_valid=bool(masked_key),
        masked_key=masked_key
    )

@router.delete("/api-keys/{provider}")
async def delete_api_key(
    provider: APIProvider,
    config_service: ConfigService = Depends(get_config_service)
):
    """Delete API key for a provider"""
    success = config_service.delete_api_key(provider)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete API key"
        )
    
    return {"message": f"API key for {provider} deleted successfully"}

@router.post("/api-keys/{provider}/validate")
async def validate_api_key(
    provider: APIProvider,
    config_service: ConfigService = Depends(get_config_service)
):
    """Validate API key for a provider"""
    api_key = config_service.get_api_key(provider)
    if not api_key:
        raise HTTPException(
            status_code=404,
            detail=f"No API key found for {provider}"
        )
    
    is_valid = config_service.validate_api_key(provider, api_key)
    
    return {
        "provider": provider,
        "is_valid": is_valid,
        "message": "API key is valid" if is_valid else "API key is invalid"
    }