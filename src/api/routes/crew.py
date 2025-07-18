from fastapi import APIRouter, HTTPException, Depends
from ..models.schemas import CrewExecutionRequest, CrewExecutionResponse, CrewExecutionStatus
from ..services.config_service import ConfigService
from ..services.crew_service import CrewService
from datetime import datetime
import uuid

router = APIRouter()

# Dependency to get config service
def get_config_service():
    return ConfigService()

# Dependency to get crew service
def get_crew_service():
    return CrewService()

@router.post("/execute", response_model=CrewExecutionResponse)
async def execute_crew(
    request: CrewExecutionRequest,
    crew_service: CrewService = Depends(get_crew_service)
):
    """Execute the requirements decomposition crew"""
    try:
        # Validate request
        if not request.prompt.strip():
            raise HTTPException(
                status_code=400,
                detail="Prompt cannot be empty"
            )
        
        # Execute crew
        response = await crew_service.execute_crew(request)
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start crew execution: {str(e)}"
        )

@router.get("/status/{execution_id}", response_model=CrewExecutionStatus)
async def get_execution_status(
    execution_id: str,
    crew_service: CrewService = Depends(get_crew_service)
):
    """Get the status of a crew execution"""
    status = crew_service.get_execution_status(execution_id)
    
    if not status:
        raise HTTPException(
            status_code=404,
            detail="Execution not found"
        )
    
    return status

@router.get("/executions")
async def get_execution_history(
    crew_service: CrewService = Depends(get_crew_service)
):
    """Get history of crew executions"""
    return crew_service.get_execution_history()

@router.delete("/executions/{execution_id}")
async def cancel_execution(
    execution_id: str,
    crew_service: CrewService = Depends(get_crew_service)
):
    """Cancel a running crew execution"""
    success = crew_service.cancel_execution(execution_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Execution not found or cannot be cancelled"
        )
    
    return {"message": f"Execution {execution_id} cancelled successfully"}