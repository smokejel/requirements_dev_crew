# CrewAI Requirements Decomposer - Test Suite

This directory contains comprehensive tests for the CrewAI Requirements Decomposer API.

## Test Structure

```
tests/
├── conftest.py                    # pytest configuration and fixtures
├── test_api_basic.py             # Basic API endpoint tests
├── test_file_operations.py       # File upload/processing tests
├── test_crew_execution.py        # CrewAI execution tests
├── test_websocket.py             # WebSocket streaming tests
├── test_integration.py           # End-to-end workflow tests
├── utils/
│   ├── api_client.py             # HTTP API client wrapper
│   └── websocket_client.py       # WebSocket client wrapper
└── fixtures/                     # Test data files (auto-generated)
```

## Installation

Install test dependencies using the optional test dependency group:

```bash
uv pip install -e ".[test]"
```

Or using pip:

```bash
pip install -e ".[test]"
```

## Running Tests

### Prerequisites

1. **API Server Running**: The FastAPI server must be running on `http://localhost:8000`
   ```bash
   cd src
   uv run uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Clean State**: Tests create and clean up their own data, but ensure the API is in a clean state.

### Basic Test Commands

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_api_basic.py

# Run with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/api

# Run only fast tests (skip slow tests)
pytest tests/ -m "not slow"

# Run only specific test categories
pytest tests/ -m "websocket"
pytest tests/ -m "integration"
```

### Test Categories

Tests are organized with markers:

- `@pytest.mark.slow` - Slow tests that take longer to run
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.websocket` - WebSocket-specific tests
- `@pytest.mark.requires_api_key` - Tests that require real API keys

### Environment Variables

- `ENABLE_API_KEY_TESTS=1` - Enable tests that require real API keys
- `OPENAI_API_KEY=sk-...` - Real OpenAI API key for full functionality tests

## Test Files Description

### `test_api_basic.py`
Tests basic API functionality:
- Health check endpoint
- Configuration management
- API key management
- Error handling
- Response format validation

### `test_file_operations.py`
Tests file operations:
- File upload (various formats)
- File processing and content extraction
- File preview functionality
- File management (list, delete)
- Error handling for invalid files

### `test_crew_execution.py`
Tests CrewAI execution:
- Crew execution with test API keys
- Execution status tracking
- Execution history
- Cancellation functionality
- Different agent configurations

### `test_websocket.py`
Tests WebSocket functionality:
- WebSocket connection management
- Real-time progress updates
- Subscription management
- Execution cancellation via WebSocket
- Error handling and reconnection

### `test_integration.py`
Tests end-to-end workflows:
- Complete workflow from file upload to execution
- Error recovery scenarios
- Concurrent operations
- System limits and boundaries
- Data consistency

## Test Data

Tests use automatically generated test data:

- **Requirements Document**: Comprehensive requirements document with functional and non-functional requirements
- **Text Files**: Simple text documents for testing file processing
- **Configuration**: Test API keys and agent configurations

## Test Results

### Expected Behavior

Most tests are designed to work with **test API keys** and will:
- ✅ Successfully test API functionality
- ✅ Test file upload and processing
- ✅ Test crew execution startup
- ❌ Fail crew execution due to invalid API keys (expected)
- ✅ Test WebSocket streaming during execution
- ✅ Test error handling and recovery

### With Real API Keys

Set `ENABLE_API_KEY_TESTS=1` and provide real API keys to test:
- ✅ Successful crew execution
- ✅ Complete workflow with real results
- ✅ Full integration testing

## Performance Testing

Performance tests check:
- API response times < 1 second
- File processing within reasonable time
- WebSocket message throughput
- Concurrent operation handling

## Debugging Tests

### View Test Output
```bash
pytest tests/ -v -s
```

### Debug Specific Test
```bash
pytest tests/test_api_basic.py::TestHealthAndInfo::test_health_check -v -s
```

### Check WebSocket Connectivity
```bash
pytest tests/test_websocket.py::TestWebSocketConnection::test_websocket_connection -v -s
```

### Test API Server Connection
```bash
curl http://localhost:8000/health
```

## Common Issues

### 1. Server Not Running
```
Error: Connection refused
```
**Solution**: Start the FastAPI server first.

### 2. WebSocket Connection Failed
```
Error: WebSocket connection failed
```
**Solution**: Ensure server is running and WebSocket endpoint is accessible.

### 3. Tests Timeout
```
Error: Test timed out
```
**Solution**: Check server performance or increase timeout values.

### 4. File Upload Failed
```
Error: File upload failed
```
**Solution**: Check file permissions and server file handling.

## Contributing

When adding new tests:

1. Use appropriate test markers (`@pytest.mark.slow`, etc.)
2. Include proper cleanup in fixtures
3. Test both success and error scenarios
4. Add integration tests for new features
5. Update this README with new test categories

## Test Coverage

The test suite covers:
- ✅ All API endpoints
- ✅ File upload and processing
- ✅ Crew execution and monitoring
- ✅ WebSocket real-time features
- ✅ Error handling and edge cases
- ✅ Concurrent operations
- ✅ Integration workflows

Target coverage: >90% for all core functionality.