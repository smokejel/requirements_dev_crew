import pytest
import asyncio
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Generator

from tests.utils.api_client import APIClient
from tests.utils.websocket_client import WebSocketTestClient

# Test configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/api/ws"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def base_url():
    """Base URL for the API server."""
    return BASE_URL

@pytest.fixture(scope="session")
def ws_url():
    """WebSocket URL for the API server."""
    return WS_URL

@pytest.fixture(scope="function")
def api_client(base_url) -> APIClient:
    """Create an API client instance."""
    return APIClient(base_url)

@pytest.fixture(scope="function")
async def websocket_client(ws_url) -> WebSocketTestClient:
    """Create a WebSocket client instance."""
    client = WebSocketTestClient(ws_url)
    await client.connect()
    yield client
    await client.disconnect()

@pytest.fixture(scope="session")
def test_files() -> Dict[str, str]:
    """Create test files for upload testing."""
    files = {}
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # Requirements document
    requirements_content = """# Emergency Communication System Requirements

## System Overview
This document outlines the requirements for an emergency communication system
that will provide reliable communication during crisis situations.

## Functional Requirements

### FR-001: Real-time Communication
The system shall provide real-time communication capabilities between
emergency responders and command centers.

### FR-002: Multi-channel Support
The system shall support multiple communication channels including:
- Voice communication
- Text messaging
- Video conferencing
- File sharing

### FR-003: High Availability
The system shall maintain 99.9% uptime and be available 24/7.

### FR-004: Scalability
The system shall handle up to 10,000 concurrent users during peak emergency situations.

## Non-Functional Requirements

### NFR-001: Performance
- System response time shall be less than 100ms
- File upload shall complete within 30 seconds for files up to 10MB
- Video calls shall maintain quality with less than 200ms latency

### NFR-002: Security
- All communications shall be encrypted end-to-end
- User authentication shall be required for all access
- System shall maintain audit logs of all activities

### NFR-003: Reliability
- System shall have automated backup and recovery mechanisms
- Data shall be replicated across multiple geographical locations
- System shall continue operating during single points of failure

## Interface Requirements

### IR-001: Web Interface
The system shall provide a responsive web interface accessible from
standard web browsers.

### IR-002: Mobile Interface
The system shall provide mobile applications for iOS and Android devices.

### IR-003: API Interface
The system shall provide RESTful APIs for third-party integrations.

## Constraints

### C-001: Regulatory Compliance
The system shall comply with federal emergency communication regulations.

### C-002: Budget Constraints
The system shall be implemented within the allocated budget of $2M.

### C-003: Timeline
The system shall be deployed within 18 months of project initiation.
"""
    
    requirements_file = os.path.join(temp_dir, "requirements.md")
    with open(requirements_file, "w") as f:
        f.write(requirements_content)
    files["requirements.md"] = requirements_file
    
    # Simple text file
    text_content = """This is a simple text document for testing file processing.
It contains multiple lines of text to test the text extraction functionality.
The file should be processed correctly by the system."""
    
    text_file = os.path.join(temp_dir, "test_document.txt")
    with open(text_file, "w") as f:
        f.write(text_content)
    files["test_document.txt"] = text_file
    
    # Test configuration
    config_content = {
        "test_api_keys": {
            "openai": "sk-test123456789abcdef",
            "anthropic": "sk-ant-test123456789abcdef",
            "google": "AIza123456789abcdef"
        },
        "test_agent_configs": {
            "requirements_analyst": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "temperature": 0.1,
                "max_tokens": 2000
            },
            "decomposition_strategist": {
                "provider": "anthropic",
                "model": "claude-3-sonnet-20240229",
                "temperature": 0.1,
                "max_tokens": 4000
            }
        }
    }
    
    import json
    config_file = os.path.join(temp_dir, "test_config.json")
    with open(config_file, "w") as f:
        json.dump(config_content, f, indent=2)
    files["test_config.json"] = config_file
    
    return files

@pytest.fixture(scope="function")
def test_config(test_files) -> Dict[str, Any]:
    """Load test configuration."""
    import json
    with open(test_files["test_config.json"]) as f:
        return json.load(f)

@pytest.fixture(scope="function")
def cleanup_uploaded_files(api_client):
    """Clean up uploaded files after tests."""
    uploaded_files = []
    
    def track_file(file_id: str):
        uploaded_files.append(file_id)
    
    yield track_file
    
    # Cleanup
    for file_id in uploaded_files:
        try:
            api_client.delete_file(file_id)
        except Exception:
            pass  # Ignore cleanup errors

@pytest.fixture(scope="function")
def cleanup_executions(api_client):
    """Clean up test executions."""
    executions = []
    
    def track_execution(execution_id: str):
        executions.append(execution_id)
    
    yield track_execution
    
    # Cleanup (cancel any running executions)
    for execution_id in executions:
        try:
            api_client.cancel_execution(execution_id)
        except Exception:
            pass  # Ignore cleanup errors

# Test markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "websocket: marks tests as websocket tests")
    config.addinivalue_line("markers", "requires_api_key: marks tests that require real API keys")

# Skip tests that require real API keys unless explicitly enabled
def pytest_runtest_setup(item):
    """Setup for test runs."""
    if "requires_api_key" in item.keywords:
        if not os.getenv("ENABLE_API_KEY_TESTS"):
            pytest.skip("Skipping test that requires real API keys (set ENABLE_API_KEY_TESTS=1 to enable)")