import asyncio
import json
import websockets
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class WebSocketTestClient:
    """WebSocket client for testing real-time functionality."""
    
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.websocket = None
        self.client_id = None
        self.connected = False
        self.messages: List[Dict[str, Any]] = []
        self.subscriptions: set = set()
        self.message_handlers: Dict[str, Callable] = {}
        self.connection_timeout = 10.0
        self.message_timeout = 5.0
    
    async def connect(self, client_id: Optional[str] = None) -> str:
        """Connect to WebSocket server."""
        try:
            # Add client_id as query parameter if provided
            url = self.ws_url
            if client_id:
                url += f"?client_id={client_id}"
            
            self.websocket = await websockets.connect(
                url,
                timeout=self.connection_timeout
            )
            self.connected = True
            
            # Start message listener
            asyncio.create_task(self._message_listener())
            
            # Wait for welcome message to get client_id
            welcome_msg = await self.wait_for_message("system", timeout=5.0)
            if welcome_msg and "Client ID:" in welcome_msg.get("message", ""):
                self.client_id = welcome_msg["message"].split("Client ID: ")[1]
            
            logger.info(f"Connected to WebSocket with client_id: {self.client_id}")
            return self.client_id
            
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from WebSocket server."""
        if self.websocket and self.connected:
            await self.websocket.close()
            self.connected = False
            logger.info("Disconnected from WebSocket")
    
    async def _message_listener(self):
        """Listen for incoming messages."""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    data["received_at"] = datetime.now().isoformat()
                    self.messages.append(data)
                    
                    # Call message handler if registered
                    msg_type = data.get("type")
                    if msg_type in self.message_handlers:
                        await self.message_handlers[msg_type](data)
                    
                    logger.debug(f"Received message: {data}")
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON message: {message}")
                    
        except websockets.exceptions.ConnectionClosed:
            self.connected = False
            logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(f"Error in message listener: {e}")
            self.connected = False
    
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send message to WebSocket server."""
        if not self.connected or not self.websocket:
            raise Exception("WebSocket not connected")
        
        try:
            await self.websocket.send(json.dumps(message))
            logger.debug(f"Sent message: {message}")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise
    
    async def subscribe(self, execution_id: str) -> None:
        """Subscribe to execution updates."""
        await self.send_message({
            "type": "subscribe",
            "execution_id": execution_id
        })
        self.subscriptions.add(execution_id)
    
    async def unsubscribe(self, execution_id: str) -> None:
        """Unsubscribe from execution updates."""
        await self.send_message({
            "type": "unsubscribe",
            "execution_id": execution_id
        })
        self.subscriptions.discard(execution_id)
    
    async def cancel_execution(self, execution_id: str) -> None:
        """Cancel execution via WebSocket."""
        await self.send_message({
            "type": "cancel_execution",
            "execution_id": execution_id
        })
    
    async def ping(self) -> None:
        """Send ping message."""
        await self.send_message({
            "type": "ping",
            "timestamp": datetime.now().isoformat()
        })
    
    async def get_status(self) -> None:
        """Get connection status."""
        await self.send_message({
            "type": "get_status"
        })
    
    def wait_for_message(self, message_type: str, timeout: float = None) -> Optional[Dict[str, Any]]:
        """Wait for a specific message type."""
        return asyncio.create_task(self._wait_for_message(message_type, timeout))
    
    async def _wait_for_message(self, message_type: str, timeout: float = None) -> Optional[Dict[str, Any]]:
        """Async implementation of wait_for_message."""
        timeout = timeout or self.message_timeout
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            for msg in reversed(self.messages):
                if msg.get("type") == message_type:
                    return msg
            await asyncio.sleep(0.1)
        
        return None
    
    async def wait_for_execution_update(self, execution_id: str, timeout: float = None) -> Optional[Dict[str, Any]]:
        """Wait for execution update message."""
        timeout = timeout or self.message_timeout
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            for msg in reversed(self.messages):
                if (msg.get("type") == "execution_update" and 
                    msg.get("execution_id") == execution_id):
                    return msg
            await asyncio.sleep(0.1)
        
        return None
    
    async def wait_for_completion(self, execution_id: str, timeout: float = 60.0) -> Optional[Dict[str, Any]]:
        """Wait for execution completion."""
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            for msg in reversed(self.messages):
                if (msg.get("type") == "execution_update" and 
                    msg.get("execution_id") == execution_id and
                    msg.get("data", {}).get("type") == "completion"):
                    return msg
            await asyncio.sleep(0.5)
        
        return None
    
    def get_messages(self, message_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all messages or messages of specific type."""
        if message_type:
            return [msg for msg in self.messages if msg.get("type") == message_type]
        return self.messages.copy()
    
    def get_execution_messages(self, execution_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a specific execution."""
        return [
            msg for msg in self.messages 
            if msg.get("execution_id") == execution_id
        ]
    
    def clear_messages(self) -> None:
        """Clear message history."""
        self.messages.clear()
    
    def add_message_handler(self, message_type: str, handler: Callable) -> None:
        """Add message handler for specific message type."""
        self.message_handlers[message_type] = handler
    
    def remove_message_handler(self, message_type: str) -> None:
        """Remove message handler."""
        if message_type in self.message_handlers:
            del self.message_handlers[message_type]
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information."""
        return {
            "client_id": self.client_id,
            "connected": self.connected,
            "ws_url": self.ws_url,
            "subscriptions": list(self.subscriptions),
            "message_count": len(self.messages)
        }
    
    async def test_connection(self) -> bool:
        """Test WebSocket connection with ping/pong."""
        try:
            await self.ping()
            pong_msg = await self._wait_for_message("pong", timeout=5.0)
            return pong_msg is not None
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    # Context manager support
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

class WebSocketTestRecorder:
    """Records WebSocket messages for testing."""
    
    def __init__(self):
        self.recordings: Dict[str, List[Dict[str, Any]]] = {}
    
    def start_recording(self, session_id: str) -> None:
        """Start recording messages for a session."""
        self.recordings[session_id] = []
    
    def record_message(self, session_id: str, message: Dict[str, Any]) -> None:
        """Record a message."""
        if session_id in self.recordings:
            self.recordings[session_id].append({
                **message,
                "recorded_at": datetime.now().isoformat()
            })
    
    def stop_recording(self, session_id: str) -> List[Dict[str, Any]]:
        """Stop recording and return messages."""
        return self.recordings.pop(session_id, [])
    
    def get_recording(self, session_id: str) -> List[Dict[str, Any]]:
        """Get recorded messages without stopping."""
        return self.recordings.get(session_id, [])
    
    def clear_recordings(self) -> None:
        """Clear all recordings."""
        self.recordings.clear()

# Test utilities
async def test_websocket_connection(ws_url: str, timeout: float = 10.0) -> bool:
    """Test if WebSocket server is accessible."""
    try:
        async with WebSocketTestClient(ws_url) as client:
            return await client.test_connection()
    except Exception as e:
        logger.error(f"WebSocket connection test failed: {e}")
        return False

async def simulate_execution_streaming(client: WebSocketTestClient, execution_id: str) -> List[Dict[str, Any]]:
    """Simulate streaming during execution and return captured messages."""
    messages = []
    
    # Subscribe to execution
    await client.subscribe(execution_id)
    
    # Record messages for 10 seconds or until completion
    start_time = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start_time < 10.0:
        # Check for completion
        completion_msg = await client.wait_for_completion(execution_id, timeout=0.1)
        if completion_msg:
            messages.extend(client.get_execution_messages(execution_id))
            break
        
        await asyncio.sleep(0.5)
    
    return messages