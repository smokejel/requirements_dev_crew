import requests
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import time

class APIClient:
    """HTTP client for testing the CrewAI Requirements API."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
    
    def _get_json(self, response: requests.Response) -> Dict[str, Any]:
        """Extract JSON from response with error handling."""
        try:
            return response.json()
        except json.JSONDecodeError:
            raise Exception(f"Invalid JSON response: {response.text}")
    
    # Health and info endpoints
    def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        response = self._make_request('GET', '/health')
        response.raise_for_status()
        return self._get_json(response)
    
    def get_openapi_spec(self) -> Dict[str, Any]:
        """Get OpenAPI specification."""
        response = self._make_request('GET', '/openapi.json')
        response.raise_for_status()
        return self._get_json(response)
    
    # Configuration endpoints
    def get_full_config(self) -> Dict[str, Any]:
        """Get full configuration."""
        response = self._make_request('GET', '/api/config/')
        response.raise_for_status()
        return self._get_json(response)
    
    def get_agent_configs(self) -> Dict[str, Any]:
        """Get agent configurations."""
        response = self._make_request('GET', '/api/config/agents')
        response.raise_for_status()
        return self._get_json(response)
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get specific agent configuration."""
        response = self._make_request('GET', f'/api/config/agents/{agent_name}')
        response.raise_for_status()
        return self._get_json(response)
    
    def update_agent_config(self, agent_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update agent configuration."""
        response = self._make_request('POST', f'/api/config/agents/{agent_name}', json=config)
        response.raise_for_status()
        return self._get_json(response)
    
    def get_model_options(self) -> Dict[str, List[str]]:
        """Get available model options."""
        response = self._make_request('GET', '/api/config/model-options')
        response.raise_for_status()
        return self._get_json(response)
    
    def get_agent_types(self) -> Dict[str, str]:
        """Get available agent types."""
        response = self._make_request('GET', '/api/config/agent-types')
        response.raise_for_status()
        return self._get_json(response)
    
    # API key management
    def store_api_key(self, provider: str, api_key: str) -> Dict[str, Any]:
        """Store API key for provider."""
        data = {
            "provider": provider,
            "api_key": api_key
        }
        response = self._make_request('POST', '/api/auth/api-keys', json=data)
        response.raise_for_status()
        return self._get_json(response)
    
    def get_api_keys(self) -> Dict[str, str]:
        """Get all API keys (masked)."""
        response = self._make_request('GET', '/api/auth/api-keys')
        response.raise_for_status()
        return self._get_json(response)
    
    def get_api_key(self, provider: str) -> Dict[str, Any]:
        """Get specific API key."""
        response = self._make_request('GET', f'/api/auth/api-keys/{provider}')
        response.raise_for_status()
        return self._get_json(response)
    
    def delete_api_key(self, provider: str) -> Dict[str, Any]:
        """Delete API key."""
        response = self._make_request('DELETE', f'/api/auth/api-keys/{provider}')
        response.raise_for_status()
        return self._get_json(response)
    
    def validate_api_key(self, provider: str) -> Dict[str, Any]:
        """Validate API key."""
        response = self._make_request('POST', f'/api/auth/api-keys/{provider}/validate')
        response.raise_for_status()
        return self._get_json(response)
    
    # File operations
    def upload_file(self, file_path: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """Upload a file."""
        if filename is None:
            filename = Path(file_path).name
        
        with open(file_path, 'rb') as f:
            files = {'file': (filename, f)}
            # Remove content-type header for file uploads
            headers = {k: v for k, v in self.session.headers.items() if k.lower() != 'content-type'}
            response = requests.post(
                f"{self.base_url}/api/files/upload",
                files=files,
                headers=headers
            )
        
        response.raise_for_status()
        return self._get_json(response)
    
    def get_files(self) -> List[Dict[str, Any]]:
        """Get list of uploaded files."""
        response = self._make_request('GET', '/api/files/')
        response.raise_for_status()
        return self._get_json(response)
    
    def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """Get file information."""
        response = self._make_request('GET', f'/api/files/{file_id}')
        response.raise_for_status()
        return self._get_json(response)
    
    def delete_file(self, file_id: str) -> Dict[str, Any]:
        """Delete a file."""
        response = self._make_request('DELETE', f'/api/files/{file_id}')
        response.raise_for_status()
        return self._get_json(response)
    
    def preview_file(self, file_id: str) -> Dict[str, Any]:
        """Get file preview."""
        response = self._make_request('GET', f'/api/files/{file_id}/preview')
        response.raise_for_status()
        return self._get_json(response)
    
    def process_file(self, file_id: str) -> Dict[str, Any]:
        """Process a file."""
        response = self._make_request('POST', f'/api/files/{file_id}/process')
        response.raise_for_status()
        return self._get_json(response)
    
    # Crew execution
    def execute_crew(self, execution_request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute crew."""
        response = self._make_request('POST', '/api/crew/execute', json=execution_request)
        response.raise_for_status()
        return self._get_json(response)
    
    def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Get execution status."""
        response = self._make_request('GET', f'/api/crew/status/{execution_id}')
        response.raise_for_status()
        return self._get_json(response)
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get execution history."""
        response = self._make_request('GET', '/api/crew/executions')
        response.raise_for_status()
        return self._get_json(response)
    
    def cancel_execution(self, execution_id: str) -> Dict[str, Any]:
        """Cancel execution."""
        response = self._make_request('DELETE', f'/api/crew/executions/{execution_id}')
        response.raise_for_status()
        return self._get_json(response)
    
    # WebSocket info
    def get_websocket_info(self) -> Dict[str, Any]:
        """Get WebSocket connection info."""
        response = self._make_request('GET', '/api/ws/info')
        response.raise_for_status()
        return self._get_json(response)
    
    def websocket_broadcast(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Broadcast message to WebSocket clients."""
        response = self._make_request('POST', '/api/ws/broadcast', json=message)
        response.raise_for_status()
        return self._get_json(response)
    
    def websocket_cleanup(self) -> Dict[str, Any]:
        """Clean up WebSocket connections."""
        response = self._make_request('POST', '/api/ws/cleanup')
        response.raise_for_status()
        return self._get_json(response)
    
    # Utility methods
    def wait_for_execution(self, execution_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Wait for execution to complete."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_execution_status(execution_id)
            if status.get('status') in ['completed', 'failed', 'cancelled']:
                return status
            time.sleep(1)
        
        raise TimeoutError(f"Execution {execution_id} did not complete within {timeout} seconds")
    
    def upload_test_files(self, test_files: Dict[str, str]) -> Dict[str, str]:
        """Upload test files and return file IDs."""
        file_ids = {}
        
        for name, path in test_files.items():
            if name.endswith('.json'):
                continue  # Skip config files
            
            result = self.upload_file(path, name)
            file_ids[name] = result['file_id']
        
        return file_ids
    
    def setup_test_api_keys(self, test_config: Dict[str, Any]) -> None:
        """Set up test API keys."""
        for provider, api_key in test_config['test_api_keys'].items():
            self.store_api_key(provider, api_key)