import asyncio
import json
import logging
from typing import Dict, Set, Any, Optional, List
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class WebSocketConnection:
    """Represents a WebSocket connection"""
    
    def __init__(self, websocket: WebSocket, client_id: str):
        self.websocket = websocket
        self.client_id = client_id
        self.connected_at = datetime.now()
        self.subscriptions: Set[str] = set()  # Execution IDs this client is subscribed to
        self.is_active = True
    
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """Send a message to the client"""
        try:
            await self.websocket.send_text(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Error sending message to client {self.client_id}: {e}")
            self.is_active = False
            return False
    
    async def send_execution_update(self, execution_id: str, update: Dict[str, Any]) -> bool:
        """Send an execution update to the client"""
        message = {
            "type": "execution_update",
            "execution_id": execution_id,
            "timestamp": datetime.now().isoformat(),
            "data": update
        }
        return await self.send_message(message)
    
    async def send_error(self, error_message: str, execution_id: Optional[str] = None) -> bool:
        """Send an error message to the client"""
        message = {
            "type": "error",
            "timestamp": datetime.now().isoformat(),
            "error": error_message
        }
        if execution_id:
            message["execution_id"] = execution_id
        return await self.send_message(message)
    
    async def send_system_message(self, message: str) -> bool:
        """Send a system message to the client"""
        msg = {
            "type": "system",
            "timestamp": datetime.now().isoformat(),
            "message": message
        }
        return await self.send_message(msg)
    
    def subscribe_to_execution(self, execution_id: str):
        """Subscribe this connection to updates for a specific execution"""
        self.subscriptions.add(execution_id)
    
    def unsubscribe_from_execution(self, execution_id: str):
        """Unsubscribe this connection from updates for a specific execution"""
        self.subscriptions.discard(execution_id)
    
    def is_subscribed_to(self, execution_id: str) -> bool:
        """Check if this connection is subscribed to an execution"""
        return execution_id in self.subscriptions

class WebSocketManager:
    """Manages WebSocket connections and message broadcasting"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WebSocketManager, cls).__new__(cls)
            cls._instance.connections = {}
            cls._instance.execution_subscribers = {}
        return cls._instance
    
    def __init__(self):
        # Only initialize once
        if not hasattr(self, 'initialized'):
            self.connections: Dict[str, WebSocketConnection] = {}
            self.execution_subscribers: Dict[str, Set[str]] = {}  # execution_id -> set of client_ids
            self.initialized = True
    
    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None) -> str:
        """Accept a new WebSocket connection"""
        if not client_id:
            client_id = str(uuid.uuid4())
        
        await websocket.accept()
        
        connection = WebSocketConnection(websocket, client_id)
        self.connections[client_id] = connection
        
        # Send welcome message
        await connection.send_system_message(f"Connected to CrewAI Requirements API. Client ID: {client_id}")
        
        logger.info(f"WebSocket client {client_id} connected")
        return client_id
    
    async def disconnect(self, client_id: str):
        """Disconnect a WebSocket client"""
        if client_id in self.connections:
            connection = self.connections[client_id]
            
            # Remove from all execution subscriptions
            for execution_id in list(connection.subscriptions):
                self.unsubscribe_from_execution(client_id, execution_id)
            
            # Remove connection
            del self.connections[client_id]
            
            logger.info(f"WebSocket client {client_id} disconnected")
    
    async def subscribe_to_execution(self, client_id: str, execution_id: str) -> bool:
        """Subscribe a client to execution updates"""
        if client_id not in self.connections:
            return False
        
        connection = self.connections[client_id]
        connection.subscribe_to_execution(execution_id)
        
        # Add to execution subscribers
        if execution_id not in self.execution_subscribers:
            self.execution_subscribers[execution_id] = set()
        self.execution_subscribers[execution_id].add(client_id)
        
        await connection.send_system_message(f"Subscribed to execution {execution_id}")
        return True
    
    async def unsubscribe_from_execution(self, client_id: str, execution_id: str) -> bool:
        """Unsubscribe a client from execution updates"""
        if client_id not in self.connections:
            return False
        
        connection = self.connections[client_id]
        connection.unsubscribe_from_execution(execution_id)
        
        # Remove from execution subscribers
        if execution_id in self.execution_subscribers:
            self.execution_subscribers[execution_id].discard(client_id)
            if not self.execution_subscribers[execution_id]:
                del self.execution_subscribers[execution_id]
        
        await connection.send_system_message(f"Unsubscribed from execution {execution_id}")
        return True
    
    async def broadcast_execution_update(self, execution_id: str, update: Dict[str, Any]):
        """Broadcast an execution update to all subscribed clients"""
        if execution_id not in self.execution_subscribers:
            return
        
        # Get all clients subscribed to this execution
        subscriber_ids = list(self.execution_subscribers[execution_id])
        
        # Send update to each subscriber
        for client_id in subscriber_ids:
            if client_id in self.connections:
                connection = self.connections[client_id]
                success = await connection.send_execution_update(execution_id, update)
                
                if not success:
                    # Connection failed, remove it
                    await self.disconnect(client_id)
    
    async def send_to_client(self, client_id: str, message: Dict[str, Any]) -> bool:
        """Send a message to a specific client"""
        if client_id not in self.connections:
            return False
        
        connection = self.connections[client_id]
        return await connection.send_message(message)
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients"""
        client_ids = list(self.connections.keys())
        
        for client_id in client_ids:
            connection = self.connections[client_id]
            success = await connection.send_message(message)
            
            if not success:
                # Connection failed, remove it
                await self.disconnect(client_id)
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.connections)
    
    def get_execution_subscriber_count(self, execution_id: str) -> int:
        """Get the number of clients subscribed to an execution"""
        return len(self.execution_subscribers.get(execution_id, set()))
    
    def get_connection_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a connection"""
        if client_id not in self.connections:
            return None
        
        connection = self.connections[client_id]
        return {
            "client_id": client_id,
            "connected_at": connection.connected_at.isoformat(),
            "subscriptions": list(connection.subscriptions),
            "is_active": connection.is_active
        }
    
    def get_all_connections_info(self) -> List[Dict[str, Any]]:
        """Get information about all connections"""
        return [
            self.get_connection_info(client_id)
            for client_id in self.connections.keys()
        ]
    
    async def cleanup_inactive_connections(self):
        """Remove inactive connections"""
        inactive_clients = [
            client_id for client_id, connection in self.connections.items()
            if not connection.is_active
        ]
        
        for client_id in inactive_clients:
            await self.disconnect(client_id)
        
        return len(inactive_clients)

# Global instance
websocket_manager = WebSocketManager()