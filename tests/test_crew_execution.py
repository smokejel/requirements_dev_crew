import pytest
import time
import requests
from tests.utils.api_client import APIClient

class TestCrewExecutionBasic:
    """Test basic crew execution functionality."""
    
    def test_crew_execution_with_test_keys(self, api_client: APIClient, test_config, cleanup_executions):
        """Test crew execution with test API keys (expected to fail)."""
        # Set up test API keys
        api_client.setup_test_api_keys(test_config)
        
        # Create execution request
        execution_request = {
            "prompt": "Test prompt for crew execution",
            "uploaded_files": [],
            "agent_configs": test_config["test_agent_configs"],
            "execution_mode": "run"
        }
        
        # Execute crew
        response = api_client.execute_crew(execution_request)
        execution_id = response["execution_id"]
        cleanup_executions(execution_id)
        
        # Verify response
        assert "execution_id" in response
        assert response["status"] == "pending"
        assert "started_at" in response
        assert "Crew execution started" in response["message"]
        
        # Wait a bit and check status
        time.sleep(2)
        status = api_client.get_execution_status(execution_id)
        
        # Should fail with test API keys
        assert status["execution_id"] == execution_id
        assert status["status"] == "failed"
        assert "error" in status
        assert "AuthenticationError" in status["error"] or "API key" in status["error"]
    
    def test_crew_execution_invalid_request(self, api_client: APIClient):
        """Test crew execution with invalid request."""
        # Empty prompt should fail
        execution_request = {
            "prompt": "",
            "uploaded_files": [],
            "agent_configs": {
                "requirements_analyst": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "temperature": 0.1,
                    "max_tokens": 2000
                }
            },
            "execution_mode": "run"
        }
        
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            api_client.execute_crew(execution_request)
        
        assert exc_info.value.response.status_code == 400
        assert "empty" in exc_info.value.response.json()["detail"]
    
    def test_crew_execution_with_files(self, api_client: APIClient, test_files, test_config, cleanup_executions, cleanup_uploaded_files):
        """Test crew execution with uploaded files."""
        # Upload a file first
        file_path = test_files["requirements.md"]
        upload_response = api_client.upload_file(file_path)
        file_id = upload_response["file_id"]
        cleanup_uploaded_files(file_id)
        
        # Set up test API keys
        api_client.setup_test_api_keys(test_config)
        
        # Create execution request with file
        execution_request = {
            "prompt": "Analyze the uploaded requirements document",
            "uploaded_files": [file_id],
            "agent_configs": test_config["test_agent_configs"],
            "execution_mode": "run"
        }
        
        # Execute crew
        response = api_client.execute_crew(execution_request)
        execution_id = response["execution_id"]
        cleanup_executions(execution_id)
        
        assert "execution_id" in response
        assert response["status"] == "pending"
        
        # Wait and check status
        time.sleep(2)
        status = api_client.get_execution_status(execution_id)
        
        # Should fail with test API keys but should have processed the file
        assert status["execution_id"] == execution_id
        assert status["status"] == "failed"
        assert "error" in status

class TestExecutionStatus:
    """Test execution status tracking."""
    
    def test_get_execution_status(self, api_client: APIClient, test_config, cleanup_executions):
        """Test getting execution status."""
        # Set up test API keys
        api_client.setup_test_api_keys(test_config)
        
        # Start execution
        execution_request = {
            "prompt": "Test status tracking",
            "uploaded_files": [],
            "agent_configs": test_config["test_agent_configs"],
            "execution_mode": "run"
        }
        
        response = api_client.execute_crew(execution_request)
        execution_id = response["execution_id"]
        cleanup_executions(execution_id)
        
        # Get initial status
        status = api_client.get_execution_status(execution_id)
        
        assert status["execution_id"] == execution_id
        assert status["status"] in ["pending", "running", "failed"]
        assert "progress" in status
        assert 0.0 <= status["progress"] <= 1.0
        
        # Check for presence of other fields
        assert "current_agent" in status
        assert "current_task" in status
        assert "output" in status
    
    def test_get_nonexistent_execution_status(self, api_client: APIClient):
        """Test getting status for non-existent execution."""
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            api_client.get_execution_status("nonexistent-execution-id")
        
        assert exc_info.value.response.status_code == 404
    
    def test_execution_progress_tracking(self, api_client: APIClient, test_config, cleanup_executions):
        """Test that execution progress is tracked."""
        # Set up test API keys
        api_client.setup_test_api_keys(test_config)
        
        # Start execution
        execution_request = {
            "prompt": "Test progress tracking",
            "uploaded_files": [],
            "agent_configs": test_config["test_agent_configs"],
            "execution_mode": "run"
        }
        
        response = api_client.execute_crew(execution_request)
        execution_id = response["execution_id"]
        cleanup_executions(execution_id)
        
        # Track progress over time
        progress_values = []
        
        for i in range(5):
            time.sleep(0.5)
            status = api_client.get_execution_status(execution_id)
            progress_values.append(status["progress"])
            
            if status["status"] in ["completed", "failed", "cancelled"]:
                break
        
        # Should see progress changes
        assert len(progress_values) > 0
        # Final progress should be 1.0 for completed/failed executions
        if status["status"] in ["completed", "failed"]:
            assert status["progress"] == 1.0

class TestExecutionHistory:
    """Test execution history functionality."""
    
    def test_get_execution_history(self, api_client: APIClient, test_config, cleanup_executions):
        """Test getting execution history."""
        # Set up test API keys
        api_client.setup_test_api_keys(test_config)
        
        # Start multiple executions
        execution_ids = []
        for i in range(2):
            execution_request = {
                "prompt": f"Test execution {i+1}",
                "uploaded_files": [],
                "agent_configs": test_config["test_agent_configs"],
                "execution_mode": "run"
            }
            
            response = api_client.execute_crew(execution_request)
            execution_ids.append(response["execution_id"])
            cleanup_executions(response["execution_id"])
        
        # Wait for executions to start
        time.sleep(2)
        
        # Get execution history
        history = api_client.get_execution_history()
        
        assert isinstance(history, list)
        assert len(history) >= 2
        
        # Check that our executions are in the history
        history_ids = [exec["execution_id"] for exec in history]
        for execution_id in execution_ids:
            assert execution_id in history_ids
        
        # Check history entry format
        for entry in history:
            assert "execution_id" in entry
            assert "status" in entry
            assert "started_at" in entry
            assert "progress" in entry
            assert entry["status"] in ["pending", "running", "completed", "failed", "cancelled"]

class TestExecutionCancellation:
    """Test execution cancellation functionality."""
    
    def test_cancel_pending_execution(self, api_client: APIClient, test_config):
        """Test cancelling a pending execution."""
        # Set up test API keys
        api_client.setup_test_api_keys(test_config)
        
        # Start execution
        execution_request = {
            "prompt": "Test cancellation",
            "uploaded_files": [],
            "agent_configs": test_config["test_agent_configs"],
            "execution_mode": "run"
        }
        
        response = api_client.execute_crew(execution_request)
        execution_id = response["execution_id"]
        
        # Cancel immediately
        cancel_response = api_client.cancel_execution(execution_id)
        assert "cancelled successfully" in cancel_response["message"]
        
        # Check that it's cancelled
        status = api_client.get_execution_status(execution_id)
        assert status["status"] == "cancelled"
        assert status["completed_at"] is not None
    
    def test_cancel_completed_execution(self, api_client: APIClient, test_config, cleanup_executions):
        """Test cancelling a completed execution."""
        # Set up test API keys
        api_client.setup_test_api_keys(test_config)
        
        # Start execution
        execution_request = {
            "prompt": "Test cancellation after completion",
            "uploaded_files": [],
            "agent_configs": test_config["test_agent_configs"],
            "execution_mode": "run"
        }
        
        response = api_client.execute_crew(execution_request)
        execution_id = response["execution_id"]
        cleanup_executions(execution_id)
        
        # Wait for completion (should fail with test keys)
        final_status = api_client.wait_for_execution(execution_id, timeout=10)
        assert final_status["status"] in ["completed", "failed"]
        
        # Try to cancel completed execution
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            api_client.cancel_execution(execution_id)
        
        assert exc_info.value.response.status_code == 404
    
    def test_cancel_nonexistent_execution(self, api_client: APIClient):
        """Test cancelling non-existent execution."""
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            api_client.cancel_execution("nonexistent-execution-id")
        
        assert exc_info.value.response.status_code == 404

class TestExecutionWithDifferentConfigs:
    """Test execution with different agent configurations."""
    
    def test_single_agent_execution(self, api_client: APIClient, test_config, cleanup_executions):
        """Test execution with single agent."""
        # Set up test API keys
        api_client.setup_test_api_keys(test_config)
        
        # Execute with only one agent
        execution_request = {
            "prompt": "Single agent test",
            "uploaded_files": [],
            "agent_configs": {
                "requirements_analyst": test_config["test_agent_configs"]["requirements_analyst"]
            },
            "execution_mode": "run"
        }
        
        response = api_client.execute_crew(execution_request)
        execution_id = response["execution_id"]
        cleanup_executions(execution_id)
        
        assert "execution_id" in response
        assert response["status"] == "pending"
    
    def test_multiple_agent_execution(self, api_client: APIClient, test_config, cleanup_executions):
        """Test execution with multiple agents."""
        # Set up test API keys
        api_client.setup_test_api_keys(test_config)
        
        # Execute with multiple agents
        execution_request = {
            "prompt": "Multi-agent test",
            "uploaded_files": [],
            "agent_configs": test_config["test_agent_configs"],
            "execution_mode": "run"
        }
        
        response = api_client.execute_crew(execution_request)
        execution_id = response["execution_id"]
        cleanup_executions(execution_id)
        
        assert "execution_id" in response
        assert response["status"] == "pending"
    
    def test_different_model_configurations(self, api_client: APIClient, test_config, cleanup_executions):
        """Test execution with different model configurations."""
        # Set up test API keys
        api_client.setup_test_api_keys(test_config)
        
        # Configure different models
        custom_configs = {
            "requirements_analyst": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "temperature": 0.0,
                "max_tokens": 1000
            },
            "decomposition_strategist": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "temperature": 0.5,
                "max_tokens": 3000
            }
        }
        
        execution_request = {
            "prompt": "Different model configs test",
            "uploaded_files": [],
            "agent_configs": custom_configs,
            "execution_mode": "run"
        }
        
        response = api_client.execute_crew(execution_request)
        execution_id = response["execution_id"]
        cleanup_executions(execution_id)
        
        assert "execution_id" in response
        assert response["status"] == "pending"

@pytest.mark.requires_api_key
class TestExecutionWithRealKeys:
    """Test execution with real API keys (only run if explicitly enabled)."""
    
    def test_successful_execution_with_real_keys(self, api_client: APIClient, cleanup_executions):
        """Test successful execution with real API keys."""
        # This test only runs if ENABLE_API_KEY_TESTS=1 is set
        import os
        
        real_api_key = os.getenv("OPENAI_API_KEY")
        if not real_api_key:
            pytest.skip("Real OpenAI API key not provided")
        
        # Store real API key
        api_client.store_api_key("openai", real_api_key)
        
        # Execute with real key
        execution_request = {
            "prompt": "Provide a brief analysis of system requirements",
            "uploaded_files": [],
            "agent_configs": {
                "requirements_analyst": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "temperature": 0.1,
                    "max_tokens": 1000
                }
            },
            "execution_mode": "run"
        }
        
        response = api_client.execute_crew(execution_request)
        execution_id = response["execution_id"]
        cleanup_executions(execution_id)
        
        # Wait for completion
        final_status = api_client.wait_for_execution(execution_id, timeout=60)
        
        # Should complete successfully
        assert final_status["status"] == "completed"
        assert final_status["progress"] == 1.0
        assert len(final_status["output"]) > 0
        assert final_status["error"] is None

class TestExecutionErrorHandling:
    """Test error handling in crew execution."""
    
    def test_execution_with_missing_api_key(self, api_client: APIClient, cleanup_executions):
        """Test execution without API key."""
        execution_request = {
            "prompt": "Test without API key",
            "uploaded_files": [],
            "agent_configs": {
                "requirements_analyst": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "temperature": 0.1,
                    "max_tokens": 2000
                }
            },
            "execution_mode": "run"
        }
        
        response = api_client.execute_crew(execution_request)
        execution_id = response["execution_id"]
        cleanup_executions(execution_id)
        
        # Should fail due to missing API key
        final_status = api_client.wait_for_execution(execution_id, timeout=10)
        assert final_status["status"] == "failed"
        assert "API key" in final_status["error"] or "key" in final_status["error"]
    
    def test_execution_with_invalid_file_id(self, api_client: APIClient, test_config, cleanup_executions):
        """Test execution with invalid file ID."""
        # Set up test API keys
        api_client.setup_test_api_keys(test_config)
        
        execution_request = {
            "prompt": "Test with invalid file ID",
            "uploaded_files": ["invalid-file-id"],
            "agent_configs": test_config["test_agent_configs"],
            "execution_mode": "run"
        }
        
        response = api_client.execute_crew(execution_request)
        execution_id = response["execution_id"]
        cleanup_executions(execution_id)
        
        # Should handle invalid file ID gracefully
        assert "execution_id" in response
        assert response["status"] == "pending"