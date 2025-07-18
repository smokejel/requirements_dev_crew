import asyncio
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import logging

# Add the src directory to the path so we can import requirement_dev
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from requirement_dev.crew import RequirementDev
from requirement_dev.main import run as original_run
from ..models.schemas import (
    CrewExecutionRequest, 
    CrewExecutionResponse, 
    CrewExecutionStatus,
    AgentConfig,
    APIProvider
)
from .config_service import ConfigService
from .file_processor import FileProcessor
from .websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

class CrewExecutionManager:
    """Manages crew execution state and progress"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CrewExecutionManager, cls).__new__(cls)
            cls._instance.executions = {}
            cls._instance.callbacks = {}
        return cls._instance
    
    def __init__(self):
        # Only initialize once
        if not hasattr(self, 'initialized'):
            self.executions: Dict[str, Dict[str, Any]] = {}
            self.callbacks: Dict[str, List[Callable]] = {}
            self.initialized = True
    
    def create_execution(self, execution_id: str, request: CrewExecutionRequest) -> None:
        """Create a new execution record"""
        self.executions[execution_id] = {
            "id": execution_id,
            "status": "pending",
            "progress": 0.0,
            "current_agent": None,
            "current_task": None,
            "output": "",
            "error": None,
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "request": request
        }
        self.callbacks[execution_id] = []
    
    def update_execution(self, execution_id: str, **kwargs) -> None:
        """Update execution state"""
        if execution_id in self.executions:
            self.executions[execution_id].update(kwargs)
            
            # Notify callbacks
            for callback in self.callbacks.get(execution_id, []):
                try:
                    callback(self.executions[execution_id])
                except Exception as e:
                    logger.error(f"Callback error for execution {execution_id}: {e}")
            
            # Send WebSocket update
            asyncio.create_task(self._send_websocket_update(execution_id, kwargs))
    
    async def _send_websocket_update(self, execution_id: str, update: Dict[str, Any]) -> None:
        """Send WebSocket update for execution"""
        try:
            await websocket_manager.broadcast_execution_update(execution_id, update)
        except Exception as e:
            logger.error(f"Error sending WebSocket update for execution {execution_id}: {e}")
    
    def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution state"""
        return self.executions.get(execution_id)
    
    def add_callback(self, execution_id: str, callback: Callable) -> None:
        """Add progress callback"""
        if execution_id not in self.callbacks:
            self.callbacks[execution_id] = []
        self.callbacks[execution_id].append(callback)
    
    def complete_execution(self, execution_id: str, output: str, error: Optional[str] = None) -> None:
        """Mark execution as completed"""
        status = "failed" if error else "completed"
        self.update_execution(
            execution_id,
            status=status,
            progress=1.0,
            output=output,
            error=error,
            completed_at=datetime.now().isoformat()
        )
        
        # Send final WebSocket update
        asyncio.create_task(self._send_completion_update(execution_id, output, error))
    
    async def _send_completion_update(self, execution_id: str, output: str, error: Optional[str] = None) -> None:
        """Send completion update via WebSocket"""
        try:
            update = {
                "type": "completion",
                "status": "failed" if error else "completed",
                "output": output,
                "error": error,
                "completed_at": datetime.now().isoformat()
            }
            await websocket_manager.broadcast_execution_update(execution_id, update)
        except Exception as e:
            logger.error(f"Error sending completion update for execution {execution_id}: {e}")

class CrewService:
    """Service for managing CrewAI integration"""
    
    def __init__(self):
        self.config_service = ConfigService()
        self.file_processor = FileProcessor()
        self.execution_manager = CrewExecutionManager()
    
    async def execute_crew(self, request: CrewExecutionRequest) -> CrewExecutionResponse:
        """Execute the requirements decomposition crew"""
        execution_id = str(uuid.uuid4())
        
        # Create execution record
        self.execution_manager.create_execution(execution_id, request)
        
        # Start execution in background
        asyncio.create_task(self._execute_crew_async(execution_id, request))
        
        return CrewExecutionResponse(
            execution_id=execution_id,
            status="pending",
            message="Crew execution started",
            started_at=datetime.now().isoformat()
        )
    
    async def _execute_crew_async(self, execution_id: str, request: CrewExecutionRequest) -> None:
        """Execute crew asynchronously"""
        try:
            # Update status to running
            self.execution_manager.update_execution(
                execution_id,
                status="running",
                progress=0.1,
                current_agent="requirements_analyst",
                current_task="Initializing execution"
            )
            
            # Prepare crew inputs
            crew_inputs = await self._prepare_crew_inputs(request)
            
            # Update progress
            self.execution_manager.update_execution(
                execution_id,
                progress=0.2,
                current_task="Preparing crew configuration"
            )
            
            # Create modified crew with API-provided configurations
            crew_instance = await self._create_configured_crew(request.agent_configs)
            
            # Update progress
            self.execution_manager.update_execution(
                execution_id,
                progress=0.3,
                current_task="Starting crew execution"
            )
            
            # Execute crew
            result = await self._run_crew_with_monitoring(
                crew_instance, 
                crew_inputs, 
                execution_id
            )
            
            # Complete execution
            self.execution_manager.complete_execution(
                execution_id,
                output=str(result),
                error=None
            )
            
        except Exception as e:
            logger.error(f"Crew execution failed for {execution_id}: {e}")
            self.execution_manager.complete_execution(
                execution_id,
                output="",
                error=str(e)
            )
    
    async def _prepare_crew_inputs(self, request: CrewExecutionRequest) -> Dict[str, Any]:
        """Prepare inputs for crew execution"""
        inputs = {
            "primary_specification": request.prompt,
            "target_system": "User-defined System",
            "decomposition_depth": "subsystem_level"
        }
        
        # Process uploaded files and add to inputs
        if request.uploaded_files:
            processed_files = []
            for file_id in request.uploaded_files:
                try:
                    processed_content = await self.file_processor.process_file(file_id)
                    if processed_content:
                        processed_files.append(processed_content)
                except Exception as e:
                    logger.warning(f"Failed to process file {file_id}: {e}")
            
            if processed_files:
                inputs["uploaded_documents"] = processed_files
        
        return inputs
    
    async def _create_configured_crew(self, agent_configs: Dict[str, AgentConfig]) -> RequirementDev:
        """Create crew instance with API-provided configurations"""
        
        # Create a custom crew class that uses our API keys
        class ConfiguredRequirementDev(RequirementDev):
            def __init__(self, api_keys: Dict[str, str], agent_configs: Dict[str, AgentConfig]):
                self.api_keys = api_keys
                self.custom_agent_configs = agent_configs
                super().__init__()
            
            def _create_llm(self, agent_name: str):
                """Override to use API-provided keys and configurations"""
                try:
                    if agent_name in self.custom_agent_configs:
                        config = self.custom_agent_configs[agent_name]
                        provider = config.provider
                        
                        # Get API key for this provider
                        api_key = self.api_keys.get(provider.value)
                        if not api_key:
                            raise ValueError(f"No API key found for provider {provider}")
                        
                        # Set environment variable for this provider
                        if provider == APIProvider.OPENAI:
                            os.environ["OPENAI_API_KEY"] = api_key
                            model_name = f"openai/{config.model}"
                        elif provider == APIProvider.ANTHROPIC:
                            os.environ["ANTHROPIC_API_KEY"] = api_key
                            model_name = f"anthropic/{config.model}"
                        elif provider == APIProvider.GOOGLE:
                            os.environ["GOOGLE_API_KEY"] = api_key
                            model_name = f"google/{config.model}"
                        else:
                            raise ValueError(f"Unsupported provider: {provider}")
                        
                        # Import LLM here to avoid circular imports
                        from crewai import LLM
                        
                        return LLM(
                            model=model_name,
                            temperature=config.temperature,
                            max_tokens=config.max_tokens,
                            timeout=120
                        )
                    else:
                        # Fall back to parent implementation
                        return super()._create_llm(agent_name)
                        
                except Exception as e:
                    logger.error(f"Failed to create LLM for {agent_name}: {e}")
                    # Fall back to parent implementation
                    return super()._create_llm(agent_name)
        
        # Get API keys from config service
        api_keys = {}
        for provider in APIProvider:
            key = self.config_service.get_api_key(provider)
            if key:
                api_keys[provider.value] = key
        
        return ConfiguredRequirementDev(api_keys, agent_configs)
    
    async def _run_crew_with_monitoring(
        self, 
        crew_instance: RequirementDev, 
        inputs: Dict[str, Any], 
        execution_id: str
    ) -> Any:
        """Run crew with progress monitoring"""
        
        # Create enhanced progress tracking
        progress_tracker = {
            "current_step": 0,
            "total_steps": 9,  # Based on the tasks in the crew
            "steps": [
                "Requirements Extraction",
                "Context Analysis", 
                "Strategy Development",
                "Functional Decomposition",
                "Non-Functional Decomposition",
                "Interface Definition",
                "Traceability Analysis",
                "Quality Validation",
                "Documentation Generation"
            ]
        }
        
        async def update_progress(step_index: int, step_name: str, status: str = "running"):
            """Update progress for a specific step"""
            progress_tracker["current_step"] = step_index
            progress = step_index / progress_tracker["total_steps"]
            
            self.execution_manager.update_execution(
                execution_id,
                current_agent=self._get_agent_for_step(step_index),
                current_task=step_name,
                progress=min(0.3 + (progress * 0.7), 1.0),  # Map to 30-100% range
                step_status=status,
                step_index=step_index,
                total_steps=progress_tracker["total_steps"]
            )
        
        # Simulate step-by-step progress since CrewAI doesn't provide detailed callbacks
        async def monitor_progress():
            """Monitor progress during execution"""
            try:
                for i, step in enumerate(progress_tracker["steps"]):
                    await update_progress(i, step, "running")
                    
                    # Wait a bit between steps (this is a simulation)
                    await asyncio.sleep(2)
                    
                    # Check if execution is still running
                    execution = self.execution_manager.get_execution(execution_id)
                    if execution and execution.get("status") not in ["running", "pending"]:
                        break
                
            except Exception as e:
                logger.error(f"Error in progress monitoring: {e}")
        
        # Start progress monitoring
        monitor_task = asyncio.create_task(monitor_progress())
        
        try:
            # Execute crew in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: crew_instance.crew().kickoff(inputs=inputs)
            )
            
            # Cancel progress monitoring
            monitor_task.cancel()
            
            return result
            
        except Exception as e:
            # Cancel progress monitoring
            monitor_task.cancel()
            raise e
    
    def _get_agent_for_step(self, step_index: int) -> str:
        """Get the agent responsible for a specific step"""
        agent_mapping = {
            0: "requirements_analyst",
            1: "decomposition_strategist", 
            2: "decomposition_strategist",
            3: "requirements_engineer",
            4: "requirements_engineer",
            5: "requirements_engineer",
            6: "requirements_engineer",
            7: "quality_assurance_agent",
            8: "documentation_specialist"
        }
        return agent_mapping.get(step_index, "unknown_agent")
    
    def get_execution_status(self, execution_id: str) -> Optional[CrewExecutionStatus]:
        """Get execution status"""
        execution = self.execution_manager.get_execution(execution_id)
        if not execution:
            return None
        
        return CrewExecutionStatus(
            execution_id=execution_id,
            status=execution["status"],
            progress=execution["progress"],
            current_agent=execution["current_agent"],
            current_task=execution["current_task"],
            output=execution["output"],
            error=execution["error"],
            completed_at=execution["completed_at"]
        )
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get execution history"""
        return [
            {
                "execution_id": exec_id,
                "status": exec_data["status"],
                "started_at": exec_data["started_at"],
                "completed_at": exec_data["completed_at"],
                "progress": exec_data["progress"]
            }
            for exec_id, exec_data in self.execution_manager.executions.items()
        ]
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution"""
        execution = self.execution_manager.get_execution(execution_id)
        if not execution:
            return False
        
        if execution["status"] in ["pending", "running"]:
            self.execution_manager.update_execution(
                execution_id,
                status="cancelled",
                completed_at=datetime.now().isoformat(),
                current_task="Execution cancelled by user"
            )
            
            # Send cancellation update via WebSocket
            asyncio.create_task(self._send_cancellation_update(execution_id))
            return True
        
        return False
    
    async def _send_cancellation_update(self, execution_id: str) -> None:
        """Send cancellation update via WebSocket"""
        try:
            update = {
                "type": "cancellation",
                "status": "cancelled",
                "message": "Execution cancelled by user",
                "cancelled_at": datetime.now().isoformat()
            }
            await websocket_manager.broadcast_execution_update(execution_id, update)
        except Exception as e:
            logger.error(f"Error sending cancellation update for execution {execution_id}: {e}")