import { useState, useEffect, useCallback, useRef } from 'react';
import { wsClient } from '../services/websocket';
import type { WebSocketMessage, ExecutionUpdate } from '../types/apiTypes';

export const useWebSocket = () => {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [executionUpdates, setExecutionUpdates] = useState<Record<string, ExecutionUpdate[]>>({});
  const wsRef = useRef(wsClient);

  useEffect(() => {
    const client = wsRef.current;

    const handleConnect = () => {
      setConnected(true);
    };

    const handleDisconnect = () => {
      setConnected(false);
    };

    const handleMessage = (message: WebSocketMessage) => {
      setMessages(prev => [...prev, message]);
    };

    const handleExecutionUpdate = (message: WebSocketMessage) => {
      if (message.execution_id) {
        setExecutionUpdates(prev => ({
          ...prev,
          [message.execution_id!]: [...(prev[message.execution_id!] || []), message.data as ExecutionUpdate]
        }));
      }
    };

    const handleError = (message: WebSocketMessage) => {
      console.error('WebSocket error:', message.error);
    };

    // Set up event handlers
    client.on('connected', handleConnect);
    client.on('disconnected', handleDisconnect);
    client.on('message', handleMessage);
    client.on('execution_update', handleExecutionUpdate);
    client.on('error', handleError);

    // Connect if not already connected
    if (!client.isConnected()) {
      client.connect().catch(console.error);
    } else {
      setConnected(true);
    }

    // Cleanup function
    return () => {
      client.off('connected', handleConnect);
      client.off('disconnected', handleDisconnect);
      client.off('message', handleMessage);
      client.off('execution_update', handleExecutionUpdate);
      client.off('error', handleError);
    };
  }, []);

  const subscribe = useCallback((executionId: string) => {
    if (connected) {
      wsRef.current.subscribe(executionId);
    }
  }, [connected]);

  const unsubscribe = useCallback((executionId: string) => {
    if (connected) {
      wsRef.current.unsubscribe(executionId);
    }
  }, [connected]);

  const cancelExecution = useCallback((executionId: string) => {
    if (connected) {
      wsRef.current.cancelExecution(executionId);
    }
  }, [connected]);

  const sendMessage = useCallback((message: any) => {
    if (connected) {
      wsRef.current.sendMessage(message);
    }
  }, [connected]);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const getExecutionUpdates = useCallback((executionId: string) => {
    return executionUpdates[executionId] || [];
  }, [executionUpdates]);

  const getLatestExecutionUpdate = useCallback((executionId: string) => {
    const updates = executionUpdates[executionId];
    return updates && updates.length > 0 ? updates[updates.length - 1] : null;
  }, [executionUpdates]);

  const waitForCompletion = useCallback((executionId: string, timeout: number = 30000) => {
    return wsRef.current.waitForCompletion(executionId, timeout);
  }, []);

  const ping = useCallback(() => {
    if (connected) {
      wsRef.current.ping();
    }
  }, [connected]);

  const getClientId = useCallback(() => {
    return wsRef.current.getClientId();
  }, []);

  const getSubscriptions = useCallback(() => {
    return wsRef.current.getSubscriptions();
  }, []);

  return {
    connected,
    messages,
    executionUpdates,
    subscribe,
    unsubscribe,
    cancelExecution,
    sendMessage,
    clearMessages,
    getExecutionUpdates,
    getLatestExecutionUpdate,
    waitForCompletion,
    ping,
    getClientId,
    getSubscriptions,
  };
};

export default useWebSocket;