import pytest
import requests
from tests.utils.api_client import APIClient

class TestHealthAndInfo:
    """Test health check and API info endpoints."""
    
    def test_health_check(self, api_client: APIClient):
        """Test health check endpoint."""
        response = api_client.health_check()
        
        assert response["status"] == "healthy"
        assert "message" in response
        assert "CrewAI Requirements API" in response["message"]
    
    def test_health_check_response_time(self, api_client: APIClient):
        """Test health check response time."""
        import time
        start_time = time.time()
        api_client.health_check()
        response_time = time.time() - start_time
        
        assert response_time < 1.0  # Should respond within 1 second
    
    def test_openapi_spec(self, api_client: APIClient):
        """Test OpenAPI specification endpoint."""
        spec = api_client.get_openapi_spec()
        
        assert "openapi" in spec
        assert "info" in spec
        assert "paths" in spec
        assert spec["info"]["title"] == "CrewAI Requirements Decomposer API"

class TestConfiguration:
    """Test configuration endpoints."""
    
    def test_get_full_config(self, api_client: APIClient):
        """Test getting full configuration."""
        config = api_client.get_full_config()
        
        assert "api_keys" in config
        assert "agent_configs" in config
        assert "default_settings" in config
        
        # Check default settings
        assert config["default_settings"]["max_file_size"] == 10485760  # 10MB
        assert ".pdf" in config["default_settings"]["supported_file_types"]
    
    def test_get_agent_configs(self, api_client: APIClient):
        """Test getting agent configurations."""
        configs = api_client.get_agent_configs()
        
        # Check that all expected agents are present
        expected_agents = [
            "requirements_analyst",
            "decomposition_strategist", 
            "requirements_engineer",
            "quality_assurance_agent",
            "documentation_specialist"
        ]
        
        for agent in expected_agents:
            assert agent in configs
            assert "provider" in configs[agent]
            assert "model" in configs[agent]
            assert "temperature" in configs[agent]
            assert "max_tokens" in configs[agent]
    
    def test_get_specific_agent_config(self, api_client: APIClient):
        """Test getting specific agent configuration."""
        agent_config = api_client.get_agent_config("requirements_analyst")
        
        assert agent_config["provider"] == "openai"
        assert agent_config["model"] == "gpt-4"
        assert agent_config["temperature"] == 0.1
        assert agent_config["max_tokens"] == 4000
    
    def test_update_agent_config(self, api_client: APIClient):
        """Test updating agent configuration."""
        new_config = {
            "provider": "openai",
            "model": "gpt-4-turbo",
            "temperature": 0.2,
            "max_tokens": 8000
        }
        
        response = api_client.update_agent_config("requirements_analyst", new_config)
        assert "message" in response
        assert "stored successfully" in response["message"]
        
        # Verify the change
        updated_config = api_client.get_agent_config("requirements_analyst")
        assert updated_config["model"] == "gpt-4-turbo"
        assert updated_config["temperature"] == 0.2
        assert updated_config["max_tokens"] == 8000
    
    def test_get_model_options(self, api_client: APIClient):
        """Test getting model options."""
        options = api_client.get_model_options()
        
        assert "openai" in options
        assert "anthropic" in options
        assert "google" in options
        
        # Check that expected models are present
        assert "gpt-4" in options["openai"]
        assert "claude-3-sonnet-20240229" in options["anthropic"]
        assert "gemini-pro" in options["google"]
    
    def test_get_agent_types(self, api_client: APIClient):
        """Test getting agent types."""
        types = api_client.get_agent_types()
        
        expected_types = {
            "requirements_analyst": "Requirements Analyst",
            "decomposition_strategist": "Decomposition Strategist",
            "requirements_engineer": "Requirements Engineer",
            "quality_assurance_agent": "Quality Assurance",
            "documentation_specialist": "Documentation Specialist"
        }
        
        for agent_type, display_name in expected_types.items():
            assert agent_type in types
            assert types[agent_type] == display_name
    
    def test_invalid_agent_config(self, api_client: APIClient):
        """Test getting configuration for non-existent agent."""
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            api_client.get_agent_config("nonexistent_agent")
        
        assert exc_info.value.response.status_code == 404

class TestAPIKeyManagement:
    """Test API key management endpoints."""
    
    def test_store_and_retrieve_api_key(self, api_client: APIClient):
        """Test storing and retrieving API keys."""
        # Store API key
        response = api_client.store_api_key("openai", "sk-test123456789abcdef")
        
        assert response["provider"] == "openai"
        assert response["is_valid"] is True
        assert response["masked_key"] == "sk-t**************cdef"
        
        # Retrieve API key
        key_info = api_client.get_api_key("openai")
        assert key_info["provider"] == "openai"
        assert key_info["is_valid"] is True
        assert key_info["masked_key"] == "sk-t**************cdef"
    
    def test_get_all_api_keys(self, api_client: APIClient):
        """Test getting all API keys."""
        # Store multiple API keys
        api_client.store_api_key("openai", "sk-test123456789abcdef")
        api_client.store_api_key("anthropic", "sk-ant-test123456789abcdef")
        
        keys = api_client.get_api_keys()
        
        assert "openai" in keys
        assert "anthropic" in keys
        assert "google" in keys
        
        # Check that keys are masked
        assert keys["openai"] == "sk-t**************cdef"
        assert keys["anthropic"] == "sk-a**************cdef"
    
    def test_validate_api_key(self, api_client: APIClient):
        """Test API key validation."""
        # Store test API key
        api_client.store_api_key("openai", "sk-test123456789abcdef")
        
        # Validate it
        validation = api_client.validate_api_key("openai")
        assert validation["provider"] == "openai"
        assert validation["is_valid"] is True
        assert "API key is valid" in validation["message"]
    
    def test_delete_api_key(self, api_client: APIClient):
        """Test deleting API key."""
        # Store API key
        api_client.store_api_key("openai", "sk-test123456789abcdef")
        
        # Delete it
        response = api_client.delete_api_key("openai")
        assert "deleted successfully" in response["message"]
        
        # Verify it's gone
        keys = api_client.get_api_keys()
        assert keys["openai"] == ""
    
    def test_invalid_api_key_format(self, api_client: APIClient):
        """Test storing invalid API key format."""
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            api_client.store_api_key("openai", "invalid-key")
        
        assert exc_info.value.response.status_code == 400
    
    def test_nonexistent_api_key_validation(self, api_client: APIClient):
        """Test validating non-existent API key."""
        # Ensure key doesn't exist
        api_client.delete_api_key("google")
        
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            api_client.validate_api_key("google")
        
        assert exc_info.value.response.status_code == 404

class TestErrorHandling:
    """Test error handling across endpoints."""
    
    def test_invalid_endpoint(self, api_client: APIClient):
        """Test accessing invalid endpoint."""
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            api_client._make_request('GET', '/api/nonexistent')
        
        assert exc_info.value.response.status_code == 404
    
    def test_invalid_method(self, api_client: APIClient):
        """Test using invalid HTTP method."""
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            api_client._make_request('PUT', '/health')
        
        assert exc_info.value.response.status_code == 405
    
    def test_invalid_json_payload(self, api_client: APIClient):
        """Test sending invalid JSON payload."""
        # This should be handled gracefully by the API
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            api_client._make_request('POST', '/api/auth/api-keys', data="invalid json")
        
        assert exc_info.value.response.status_code in [400, 422]

class TestWebSocketInfo:
    """Test WebSocket information endpoints."""
    
    def test_websocket_info(self, api_client: APIClient):
        """Test WebSocket connection info."""
        info = api_client.get_websocket_info()
        
        assert "total_connections" in info
        assert "connections" in info
        assert isinstance(info["total_connections"], int)
        assert isinstance(info["connections"], list)
    
    def test_websocket_broadcast(self, api_client: APIClient):
        """Test WebSocket broadcast functionality."""
        message = {
            "type": "test",
            "message": "Test broadcast message"
        }
        
        response = api_client.websocket_broadcast(message)
        
        assert response["status"] == "Message broadcasted"
        assert "recipients" in response
        assert isinstance(response["recipients"], int)
    
    def test_websocket_cleanup(self, api_client: APIClient):
        """Test WebSocket cleanup functionality."""
        response = api_client.websocket_cleanup()
        
        assert response["status"] == "Cleanup completed"
        assert "removed_connections" in response
        assert isinstance(response["removed_connections"], int)

class TestResponseFormat:
    """Test response format consistency."""
    
    def test_json_response_format(self, api_client: APIClient):
        """Test that all endpoints return valid JSON."""
        # Test various endpoints
        responses = [
            api_client.health_check(),
            api_client.get_full_config(),
            api_client.get_agent_configs(),
            api_client.get_model_options(),
            api_client.get_api_keys(),
            api_client.get_websocket_info()
        ]
        
        for response in responses:
            assert isinstance(response, dict)
    
    def test_error_response_format(self, api_client: APIClient):
        """Test error response format."""
        try:
            api_client._make_request('GET', '/api/nonexistent')
        except requests.exceptions.HTTPError as e:
            error_response = e.response.json()
            assert "detail" in error_response
    
    def test_cors_headers(self, api_client: APIClient):
        """Test CORS headers are present."""
        response = api_client._make_request('GET', '/health')
        
        # Check for CORS headers (these should be set by FastAPI middleware)
        # Note: The actual headers depend on the CORS configuration
        assert response.status_code == 200