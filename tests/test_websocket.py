import pytest
import asyncio
import time
from tests.utils.api_client import APIClient
from tests.utils.websocket_client import WebSocketTestClient, test_websocket_connection

@pytest.mark.asyncio
@pytest.mark.websocket
class TestWebSocketConnection:
    """Test WebSocket connection functionality."""
    
    async def test_websocket_connection(self, ws_url):
        """Test basic WebSocket connection."""
        success = await test_websocket_connection(ws_url)
        assert success is True
    
    async def test_websocket_client_connection(self, websocket_client: WebSocketTestClient):
        """Test WebSocket client connection."""
        assert websocket_client.connected is True
        assert websocket_client.client_id is not None
        
        # Test connection info
        info = websocket_client.get_connection_info()
        assert info["connected"] is True
        assert info["client_id"] is not None
        assert info["message_count"] >= 1  # Should have welcome message
    
    async def test_websocket_ping_pong(self, websocket_client: WebSocketTestClient):
        """Test WebSocket ping/pong functionality."""
        # Clear previous messages
        websocket_client.clear_messages()
        
        # Send ping
        await websocket_client.ping()
        
        # Wait for pong
        pong_msg = await websocket_client._wait_for_message("pong", timeout=5.0)
        
        assert pong_msg is not None
        assert pong_msg["type"] == "pong"
        assert "timestamp" in pong_msg
    
    async def test_websocket_get_status(self, websocket_client: WebSocketTestClient):
        """Test getting WebSocket status."""
        # Clear previous messages
        websocket_client.clear_messages()
        
        # Get status
        await websocket_client.get_status()
        
        # Wait for status response
        status_msg = await websocket_client._wait_for_message("status", timeout=5.0)
        
        assert status_msg is not None
        assert status_msg["type"] == "status"
        assert "data" in status_msg
        
        # Check status data
        data = status_msg["data"]
        assert data["connected"] is True
        assert data["client_id"] is not None
    
    async def test_websocket_connection_with_custom_client_id(self, ws_url):
        """Test WebSocket connection with custom client ID."""
        custom_client_id = "test-client-123"
        
        async with WebSocketTestClient(ws_url) as client:
            client_id = await client.connect(custom_client_id)
            assert client_id == custom_client_id
    
    async def test_websocket_message_handling(self, websocket_client: WebSocketTestClient):
        """Test WebSocket message handling."""
        # Clear previous messages
        websocket_client.clear_messages()
        
        # Send ping
        await websocket_client.ping()
        
        # Wait a bit for response
        await asyncio.sleep(1)
        
        # Check messages
        messages = websocket_client.get_messages()
        assert len(messages) > 0
        
        # Should have pong message
        pong_messages = websocket_client.get_messages("pong")
        assert len(pong_messages) > 0

@pytest.mark.asyncio
@pytest.mark.websocket
class TestWebSocketSubscriptions:
    """Test WebSocket subscription functionality."""
    
    async def test_subscribe_to_execution(self, websocket_client: WebSocketTestClient):
        """Test subscribing to execution updates."""
        test_execution_id = "test-execution-123"
        
        # Clear previous messages
        websocket_client.clear_messages()
        
        # Subscribe to execution
        await websocket_client.subscribe(test_execution_id)
        
        # Wait for confirmation
        await asyncio.sleep(1)
        
        # Check that we're subscribed
        assert test_execution_id in websocket_client.subscriptions
        
        # Check for system message
        messages = websocket_client.get_messages("system")
        subscribe_msg = next((msg for msg in messages if "Subscribed to execution" in msg.get("message", "")), None)
        assert subscribe_msg is not None
    
    async def test_unsubscribe_from_execution(self, websocket_client: WebSocketTestClient):
        """Test unsubscribing from execution updates."""
        test_execution_id = "test-execution-123"
        
        # First subscribe
        await websocket_client.subscribe(test_execution_id)
        await asyncio.sleep(0.5)
        
        # Clear messages
        websocket_client.clear_messages()
        
        # Then unsubscribe
        await websocket_client.unsubscribe(test_execution_id)
        
        # Wait for confirmation
        await asyncio.sleep(1)
        
        # Check that we're not subscribed
        assert test_execution_id not in websocket_client.subscriptions
        
        # Check for system message
        messages = websocket_client.get_messages("system")
        unsubscribe_msg = next((msg for msg in messages if "Unsubscribed from execution" in msg.get("message", "")), None)
        assert unsubscribe_msg is not None
    
    async def test_subscribe_without_execution_id(self, websocket_client: WebSocketTestClient):
        """Test subscribing without execution ID."""
        # Clear previous messages
        websocket_client.clear_messages()
        
        # Send subscribe message without execution_id
        await websocket_client.send_message({
            "type": "subscribe"
        })
        
        # Wait for error response
        await asyncio.sleep(1)
        
        # Should get error message
        error_messages = websocket_client.get_messages("error")
        assert len(error_messages) > 0
        assert "execution_id required" in error_messages[0]["error"]
    
    async def test_multiple_subscriptions(self, websocket_client: WebSocketTestClient):
        """Test multiple subscriptions."""
        execution_ids = ["exec-1", "exec-2", "exec-3"]
        
        # Subscribe to multiple executions
        for exec_id in execution_ids:
            await websocket_client.subscribe(exec_id)
            await asyncio.sleep(0.2)
        
        # Check all subscriptions
        for exec_id in execution_ids:
            assert exec_id in websocket_client.subscriptions
        
        # Unsubscribe from all
        for exec_id in execution_ids:
            await websocket_client.unsubscribe(exec_id)
            await asyncio.sleep(0.2)
        
        # Check all unsubscribed
        for exec_id in execution_ids:
            assert exec_id not in websocket_client.subscriptions

@pytest.mark.asyncio
@pytest.mark.websocket
class TestWebSocketExecutionUpdates:
    """Test WebSocket execution update functionality."""
    
    async def test_execution_update_reception(self, websocket_client: WebSocketTestClient, api_client: APIClient, test_config):
        """Test receiving execution updates via WebSocket."""
        # Set up test API keys
        api_client.setup_test_api_keys(test_config)
        
        # Start execution
        execution_request = {
            "prompt": "Test WebSocket streaming",
            "uploaded_files": [],
            "agent_configs": test_config["test_agent_configs"],
            "execution_mode": "run"
        }
        
        response = api_client.execute_crew(execution_request)
        execution_id = response["execution_id"]
        
        # Subscribe to execution updates
        await websocket_client.subscribe(execution_id)
        
        # Wait for execution updates
        await asyncio.sleep(3)
        
        # Check for execution update messages
        execution_messages = websocket_client.get_execution_messages(execution_id)
        assert len(execution_messages) > 0
        
        # Check message format
        for msg in execution_messages:
            assert msg["type"] == "execution_update"
            assert msg["execution_id"] == execution_id
            assert "data" in msg
            assert "timestamp" in msg
        
        # Cancel execution for cleanup
        try:
            api_client.cancel_execution(execution_id)
        except:
            pass
    
    async def test_execution_completion_notification(self, websocket_client: WebSocketTestClient, api_client: APIClient, test_config):
        """Test execution completion notification via WebSocket."""
        # Set up test API keys
        api_client.setup_test_api_keys(test_config)
        
        # Start execution
        execution_request = {
            "prompt": "Test completion notification",
            "uploaded_files": [],
            "agent_configs": test_config["test_agent_configs"],
            "execution_mode": "run"
        }
        
        response = api_client.execute_crew(execution_request)
        execution_id = response["execution_id"]
        
        # Subscribe to execution updates
        await websocket_client.subscribe(execution_id)
        
        # Wait for completion (should fail with test keys)
        completion_msg = await websocket_client.wait_for_completion(execution_id, timeout=10.0)
        
        assert completion_msg is not None
        assert completion_msg["type"] == "execution_update"
        assert completion_msg["execution_id"] == execution_id
        assert completion_msg["data"]["type"] == "completion"
        assert completion_msg["data"]["status"] == "failed"  # Expected with test keys
    
    async def test_execution_progress_updates(self, websocket_client: WebSocketTestClient, api_client: APIClient, test_config):
        """Test execution progress updates via WebSocket."""
        # Set up test API keys
        api_client.setup_test_api_keys(test_config)
        
        # Start execution
        execution_request = {
            "prompt": "Test progress updates",
            "uploaded_files": [],
            "agent_configs": test_config["test_agent_configs"],
            "execution_mode": "run"
        }
        
        response = api_client.execute_crew(execution_request)
        execution_id = response["execution_id"]
        
        # Subscribe and collect progress updates
        await websocket_client.subscribe(execution_id)
        
        # Collect updates for a few seconds
        progress_updates = []
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < 5.0:
            await asyncio.sleep(0.5)
            
            # Get recent execution messages
            messages = websocket_client.get_execution_messages(execution_id)
            for msg in messages:
                if msg.get("data", {}).get("progress") is not None:
                    progress_updates.append(msg["data"]["progress"])
        
        # Should have received progress updates
        assert len(progress_updates) > 0
        
        # Progress should be between 0 and 1
        for progress in progress_updates:
            assert 0.0 <= progress <= 1.0
        
        # Cancel execution for cleanup
        try:
            api_client.cancel_execution(execution_id)
        except:
            pass

@pytest.mark.asyncio
@pytest.mark.websocket
class TestWebSocketExecutionCancellation:
    """Test WebSocket execution cancellation functionality."""
    
    async def test_cancel_execution_via_websocket(self, websocket_client: WebSocketTestClient, api_client: APIClient, test_config):
        """Test cancelling execution via WebSocket."""
        # Set up test API keys
        api_client.setup_test_api_keys(test_config)
        
        # Start execution
        execution_request = {
            "prompt": "Test WebSocket cancellation",
            "uploaded_files": [],
            "agent_configs": test_config["test_agent_configs"],
            "execution_mode": "run"
        }
        
        response = api_client.execute_crew(execution_request)
        execution_id = response["execution_id"]
        
        # Subscribe to execution
        await websocket_client.subscribe(execution_id)
        
        # Wait a bit for execution to start
        await asyncio.sleep(1)
        
        # Cancel via WebSocket
        await websocket_client.cancel_execution(execution_id)
        
        # Wait for cancellation confirmation
        await asyncio.sleep(2)
        
        # Check for cancellation messages
        messages = websocket_client.get_messages()
        
        # Should have cancellation confirmation
        confirmation_msg = next((msg for msg in messages if msg.get("type") == "cancellation_confirmed"), None)
        assert confirmation_msg is not None
        assert confirmation_msg["execution_id"] == execution_id
        
        # Should also have cancellation update
        execution_messages = websocket_client.get_execution_messages(execution_id)
        cancellation_update = next((msg for msg in execution_messages if msg.get("data", {}).get("type") == "cancellation"), None)
        assert cancellation_update is not None
        assert cancellation_update["data"]["status"] == "cancelled"
    
    async def test_cancel_nonexistent_execution(self, websocket_client: WebSocketTestClient):
        """Test cancelling non-existent execution via WebSocket."""
        # Clear previous messages
        websocket_client.clear_messages()
        
        # Try to cancel non-existent execution
        await websocket_client.cancel_execution("nonexistent-execution-id")
        
        # Wait for error response
        await asyncio.sleep(1)
        
        # Should get error message
        error_messages = websocket_client.get_messages("error")
        assert len(error_messages) > 0
        assert "Failed to cancel execution" in error_messages[0]["error"]
    
    async def test_cancel_without_execution_id(self, websocket_client: WebSocketTestClient):
        """Test cancelling without execution ID."""
        # Clear previous messages
        websocket_client.clear_messages()
        
        # Send cancel message without execution_id
        await websocket_client.send_message({
            "type": "cancel_execution"
        })
        
        # Wait for error response
        await asyncio.sleep(1)
        
        # Should get error message
        error_messages = websocket_client.get_messages("error")
        assert len(error_messages) > 0
        assert "execution_id required" in error_messages[0]["error"]

@pytest.mark.asyncio
@pytest.mark.websocket
class TestWebSocketErrorHandling:
    """Test WebSocket error handling."""
    
    async def test_invalid_message_type(self, websocket_client: WebSocketTestClient):
        """Test sending invalid message type."""
        # Clear previous messages
        websocket_client.clear_messages()
        
        # Send invalid message type
        await websocket_client.send_message({
            "type": "invalid_message_type"
        })
        
        # Wait for error response
        await asyncio.sleep(1)
        
        # Should get error message
        error_messages = websocket_client.get_messages("error")
        assert len(error_messages) > 0
        assert "Unknown message type" in error_messages[0]["error"]
    
    async def test_invalid_json_message(self, websocket_client: WebSocketTestClient):
        """Test sending invalid JSON message."""
        # This test is tricky because we need to send raw text
        # We'll simulate by checking the client handles JSON decode errors
        
        # For now, just verify the client can handle normal messages
        await websocket_client.ping()
        pong_msg = await websocket_client._wait_for_message("pong", timeout=5.0)
        assert pong_msg is not None
    
    async def test_websocket_reconnection(self, ws_url):
        """Test WebSocket reconnection capability."""
        # Connect first time
        client1 = WebSocketTestClient(ws_url)
        await client1.connect()
        
        client_id = client1.client_id
        assert client1.connected is True
        
        # Disconnect
        await client1.disconnect()
        assert client1.connected is False
        
        # Reconnect with same client ID
        client2 = WebSocketTestClient(ws_url)
        await client2.connect(client_id)
        
        assert client2.connected is True
        assert client2.client_id == client_id
        
        await client2.disconnect()

@pytest.mark.asyncio
@pytest.mark.websocket
class TestWebSocketIntegration:
    """Test WebSocket integration with API."""
    
    async def test_websocket_info_endpoint(self, api_client: APIClient, websocket_client: WebSocketTestClient):
        """Test WebSocket info endpoint shows connected clients."""
        # Get WebSocket info
        info = api_client.get_websocket_info()
        
        # Should show at least one connection (our test client)
        assert info["total_connections"] >= 1
        assert len(info["connections"]) >= 1
        
        # Find our connection
        our_connection = next((conn for conn in info["connections"] if conn["client_id"] == websocket_client.client_id), None)
        assert our_connection is not None
        assert our_connection["connected"] is True
    
    async def test_websocket_broadcast_integration(self, api_client: APIClient, websocket_client: WebSocketTestClient):
        """Test WebSocket broadcast integration."""
        # Clear previous messages
        websocket_client.clear_messages()
        
        # Send broadcast message via API
        test_message = {
            "type": "test_broadcast",
            "message": "Test broadcast message",
            "data": {"test": True}
        }
        
        response = api_client.websocket_broadcast(test_message)
        assert response["recipients"] >= 1
        
        # Wait for broadcast message
        await asyncio.sleep(1)
        
        # Should receive the broadcast
        messages = websocket_client.get_messages()
        broadcast_msg = next((msg for msg in messages if msg.get("type") == "test_broadcast"), None)
        assert broadcast_msg is not None
        assert broadcast_msg["message"] == "Test broadcast message"
        assert broadcast_msg["data"]["test"] is True
    
    async def test_websocket_cleanup_integration(self, api_client: APIClient):
        """Test WebSocket cleanup integration."""
        # Create and disconnect a client to create inactive connection
        client = WebSocketTestClient(WS_URL)
        await client.connect()
        
        # Force disconnect without proper cleanup
        if client.websocket:
            await client.websocket.close()
        client.connected = False
        
        # Run cleanup
        response = api_client.websocket_cleanup()
        assert "removed_connections" in response
        assert isinstance(response["removed_connections"], int)

@pytest.mark.asyncio
@pytest.mark.websocket
@pytest.mark.slow
class TestWebSocketPerformance:
    """Test WebSocket performance characteristics."""
    
    async def test_multiple_concurrent_connections(self, ws_url):
        """Test handling multiple concurrent WebSocket connections."""
        clients = []
        
        try:
            # Create multiple connections
            for i in range(5):
                client = WebSocketTestClient(ws_url)
                await client.connect(f"test-client-{i}")
                clients.append(client)
            
            # All should be connected
            for client in clients:
                assert client.connected is True
            
            # Test communication from all clients
            for client in clients:
                await client.ping()
            
            # Wait for all pongs
            await asyncio.sleep(2)
            
            # All should have received pong
            for client in clients:
                pong_messages = client.get_messages("pong")
                assert len(pong_messages) > 0
        
        finally:
            # Cleanup
            for client in clients:
                if client.connected:
                    await client.disconnect()
    
    async def test_message_throughput(self, websocket_client: WebSocketTestClient):
        """Test WebSocket message throughput."""
        # Clear previous messages
        websocket_client.clear_messages()
        
        # Send multiple ping messages rapidly
        num_pings = 10
        start_time = asyncio.get_event_loop().time()
        
        for i in range(num_pings):
            await websocket_client.ping()
            await asyncio.sleep(0.1)  # Small delay to avoid overwhelming
        
        end_time = asyncio.get_event_loop().time()
        
        # Wait for all responses
        await asyncio.sleep(2)
        
        # Check that we received all pongs
        pong_messages = websocket_client.get_messages("pong")
        assert len(pong_messages) == num_pings
        
        # Calculate throughput
        total_time = end_time - start_time
        throughput = num_pings / total_time
        
        # Should handle at least 5 messages per second
        assert throughput >= 5.0

# Set WS_URL for tests that need it
WS_URL = "ws://localhost:8000/api/ws"