import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse
from typing import Optional

from ..services.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None),
    execution_id: Optional[str] = Query(None)
):
    """WebSocket endpoint for real-time updates"""
    try:
        # Connect client
        client_id = await websocket_manager.connect(websocket, client_id)
        
        # If execution_id is provided, subscribe to it
        if execution_id:
            await websocket_manager.subscribe_to_execution(client_id, execution_id)
        
        # Listen for messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                await handle_websocket_message(client_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected")
                break
            except json.JSONDecodeError:
                # Send error for invalid JSON
                await websocket_manager.send_to_client(
                    client_id, 
                    {
                        "type": "error",
                        "error": "Invalid JSON format"
                    }
                )
            except Exception as e:
                logger.error(f"Error handling message from client {client_id}: {e}")
                await websocket_manager.send_to_client(
                    client_id,
                    {
                        "type": "error", 
                        "error": f"Server error: {str(e)}"
                    }
                )
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    
    finally:
        # Disconnect client
        await websocket_manager.disconnect(client_id)

async def handle_websocket_message(client_id: str, message: dict):
    """Handle incoming WebSocket messages"""
    message_type = message.get("type")
    
    if message_type == "subscribe":
        # Subscribe to execution updates
        execution_id = message.get("execution_id")
        if execution_id:
            await websocket_manager.subscribe_to_execution(client_id, execution_id)
        else:
            await websocket_manager.send_to_client(
                client_id,
                {
                    "type": "error",
                    "error": "execution_id required for subscribe"
                }
            )
    
    elif message_type == "unsubscribe":
        # Unsubscribe from execution updates
        execution_id = message.get("execution_id")
        if execution_id:
            await websocket_manager.unsubscribe_from_execution(client_id, execution_id)
        else:
            await websocket_manager.send_to_client(
                client_id,
                {
                    "type": "error",
                    "error": "execution_id required for unsubscribe"
                }
            )
    
    elif message_type == "ping":
        # Respond to ping with pong
        await websocket_manager.send_to_client(
            client_id,
            {
                "type": "pong",
                "timestamp": message.get("timestamp")
            }
        )
    
    elif message_type == "get_status":
        # Get current connection status
        info = websocket_manager.get_connection_info(client_id)
        await websocket_manager.send_to_client(
            client_id,
            {
                "type": "status",
                "data": info
            }
        )
    
    elif message_type == "cancel_execution":
        # Cancel a running execution
        execution_id = message.get("execution_id")
        if execution_id:
            # Import here to avoid circular imports
            from ..services.crew_service import CrewService
            
            crew_service = CrewService()
            success = crew_service.cancel_execution(execution_id)
            
            if success:
                await websocket_manager.send_to_client(
                    client_id,
                    {
                        "type": "cancellation_confirmed",
                        "execution_id": execution_id,
                        "message": "Execution cancelled successfully"
                    }
                )
            else:
                await websocket_manager.send_to_client(
                    client_id,
                    {
                        "type": "error",
                        "error": "Failed to cancel execution or execution not found"
                    }
                )
        else:
            await websocket_manager.send_to_client(
                client_id,
                {
                    "type": "error",
                    "error": "execution_id required for cancel_execution"
                }
            )
    
    else:
        await websocket_manager.send_to_client(
            client_id,
            {
                "type": "error",
                "error": f"Unknown message type: {message_type}"
            }
        )

@router.get("/ws/info")
async def get_websocket_info():
    """Get WebSocket connection information"""
    return {
        "total_connections": websocket_manager.get_connection_count(),
        "connections": websocket_manager.get_all_connections_info()
    }

@router.get("/ws/test")
async def get_websocket_test_page():
    """Get a test page for WebSocket functionality"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CrewAI WebSocket Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            .message { margin: 5px 0; padding: 10px; border-radius: 5px; }
            .message.sent { background-color: #e3f2fd; text-align: right; }
            .message.received { background-color: #f5f5f5; }
            .message.error { background-color: #ffebee; color: #c62828; }
            .message.system { background-color: #e8f5e8; color: #2e7d32; }
            #messages { height: 400px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; }
            .controls { margin: 10px 0; }
            input, button { margin: 5px; padding: 8px; }
            button { background-color: #1976d2; color: white; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background-color: #1565c0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>CrewAI WebSocket Test</h1>
            
            <div class="controls">
                <input type="text" id="executionId" placeholder="Execution ID" />
                <button onclick="subscribe()">Subscribe</button>
                <button onclick="unsubscribe()">Unsubscribe</button>
                <button onclick="cancelExecution()">Cancel Execution</button>
                <button onclick="ping()">Ping</button>
                <button onclick="getStatus()">Get Status</button>
                <button onclick="clearMessages()">Clear</button>
            </div>
            
            <div id="messages"></div>
            
            <div class="controls">
                <span id="status">Disconnected</span>
            </div>
        </div>

        <script>
            let ws = null;
            let clientId = null;
            
            function connect() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/api/ws`;
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function(event) {
                    document.getElementById('status').textContent = 'Connected';
                    addMessage('Connected to WebSocket', 'system');
                };
                
                ws.onmessage = function(event) {
                    const message = JSON.parse(event.data);
                    handleMessage(message);
                };
                
                ws.onclose = function(event) {
                    document.getElementById('status').textContent = 'Disconnected';
                    addMessage('Disconnected from WebSocket', 'system');
                };
                
                ws.onerror = function(error) {
                    addMessage(`WebSocket error: ${error}`, 'error');
                };
            }
            
            function handleMessage(message) {
                let messageText = '';
                let messageClass = 'received';
                
                switch(message.type) {
                    case 'system':
                        messageText = `[SYSTEM] ${message.message}`;
                        messageClass = 'system';
                        break;
                    case 'execution_update':
                        messageText = `[EXEC UPDATE] ${message.execution_id}: ${JSON.stringify(message.data)}`;
                        break;
                    case 'error':
                        messageText = `[ERROR] ${message.error}`;
                        messageClass = 'error';
                        break;
                    case 'pong':
                        messageText = `[PONG] ${message.timestamp}`;
                        break;
                    case 'status':
                        messageText = `[STATUS] ${JSON.stringify(message.data)}`;
                        break;
                    case 'cancellation_confirmed':
                        messageText = `[CANCELLED] ${message.execution_id}: ${message.message}`;
                        messageClass = 'system';
                        break;
                    default:
                        messageText = JSON.stringify(message);
                }
                
                addMessage(messageText, messageClass);
            }
            
            function addMessage(text, className = 'received') {
                const messages = document.getElementById('messages');
                const div = document.createElement('div');
                div.className = `message ${className}`;
                div.textContent = text;
                messages.appendChild(div);
                messages.scrollTop = messages.scrollHeight;
            }
            
            function sendMessage(message) {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify(message));
                    addMessage(JSON.stringify(message), 'sent');
                } else {
                    addMessage('WebSocket not connected', 'error');
                }
            }
            
            function subscribe() {
                const executionId = document.getElementById('executionId').value;
                if (!executionId) {
                    addMessage('Please enter an execution ID', 'error');
                    return;
                }
                sendMessage({
                    type: 'subscribe',
                    execution_id: executionId
                });
            }
            
            function unsubscribe() {
                const executionId = document.getElementById('executionId').value;
                if (!executionId) {
                    addMessage('Please enter an execution ID', 'error');
                    return;
                }
                sendMessage({
                    type: 'unsubscribe',
                    execution_id: executionId
                });
            }
            
            function ping() {
                sendMessage({
                    type: 'ping',
                    timestamp: new Date().toISOString()
                });
            }
            
            function getStatus() {
                sendMessage({
                    type: 'get_status'
                });
            }
            
            function cancelExecution() {
                const executionId = document.getElementById('executionId').value;
                if (!executionId) {
                    addMessage('Please enter an execution ID', 'error');
                    return;
                }
                sendMessage({
                    type: 'cancel_execution',
                    execution_id: executionId
                });
            }
            
            function clearMessages() {
                document.getElementById('messages').innerHTML = '';
            }
            
            // Connect on page load
            window.onload = function() {
                connect();
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.post("/ws/broadcast")
async def broadcast_message(message: dict):
    """Broadcast a message to all connected clients (for testing)"""
    await websocket_manager.broadcast_to_all(message)
    return {"status": "Message broadcasted", "recipients": websocket_manager.get_connection_count()}

@router.post("/ws/cleanup")
async def cleanup_connections():
    """Clean up inactive connections"""
    removed = await websocket_manager.cleanup_inactive_connections()
    return {"status": "Cleanup completed", "removed_connections": removed}