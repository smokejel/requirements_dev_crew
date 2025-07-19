import type { WebSocketMessage, ExecutionUpdate } from '../types/apiTypes';

export type WebSocketEventHandler = (message: WebSocketMessage) => void;

class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private clientId: string;
  private connected: boolean = false;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelay: number = 1000;
  private eventHandlers: Map<string, WebSocketEventHandler[]> = new Map();
  private subscriptions: Set<string> = new Set();

  constructor(url: string = 'ws://localhost:8000/api/ws', clientId?: string) {
    this.url = url;
    this.clientId = clientId || this.generateClientId();
  }

  private generateClientId(): string {
    return `client-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(`${this.url}?client_id=${this.clientId}`);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.connected = true;
          this.reconnectAttempts = 0;
          this.emit('connected', { type: 'connected', data: { clientId: this.clientId } });
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.connected = false;
          this.emit('disconnected', { type: 'disconnected', data: { code: event.code, reason: event.reason } });
          
          // Attempt to reconnect if not a clean close
          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.attemptReconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.emit('error', { type: 'error', error: 'WebSocket connection error' });
          reject(error);
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  private async attemptReconnect(): Promise<void> {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`);
    
    setTimeout(async () => {
      try {
        await this.connect();
        
        // Resubscribe to all previous subscriptions
        for (const executionId of this.subscriptions) {
          await this.subscribe(executionId);
        }
      } catch (error) {
        console.error('Reconnect failed:', error);
      }
    }, delay);
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
      this.connected = false;
      this.subscriptions.clear();
    }
  }

  isConnected(): boolean {
    return this.connected && this.ws?.readyState === WebSocket.OPEN;
  }

  private handleMessage(message: WebSocketMessage): void {
    // Emit to type-specific handlers
    this.emit(message.type, message);
    
    // Emit to general message handler
    this.emit('message', message);
  }

  // Event handling
  on(event: string, handler: WebSocketEventHandler): void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, []);
    }
    this.eventHandlers.get(event)!.push(handler);
  }

  off(event: string, handler: WebSocketEventHandler): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  private emit(event: string, message: WebSocketMessage): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error('Error in event handler:', error);
        }
      });
    }
  }

  // WebSocket actions
  sendMessage(message: any): void {
    if (this.isConnected()) {
      this.ws!.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  }

  async subscribe(executionId: string): Promise<void> {
    this.sendMessage({
      type: 'subscribe',
      execution_id: executionId
    });
    this.subscriptions.add(executionId);
  }

  async unsubscribe(executionId: string): Promise<void> {
    this.sendMessage({
      type: 'unsubscribe',
      execution_id: executionId
    });
    this.subscriptions.delete(executionId);
  }

  async cancelExecution(executionId: string): Promise<void> {
    this.sendMessage({
      type: 'cancel_execution',
      execution_id: executionId
    });
  }

  ping(): void {
    this.sendMessage({
      type: 'ping'
    });
  }

  getStatus(): void {
    this.sendMessage({
      type: 'get_status'
    });
  }

  // Utility methods
  waitForMessage(type: string, timeout: number = 5000): Promise<WebSocketMessage> {
    return new Promise((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        this.off(type, handler);
        reject(new Error(`Timeout waiting for ${type} message`));
      }, timeout);

      const handler = (message: WebSocketMessage) => {
        clearTimeout(timeoutId);
        this.off(type, handler);
        resolve(message);
      };

      this.on(type, handler);
    });
  }

  waitForCompletion(executionId: string, timeout: number = 30000): Promise<WebSocketMessage> {
    return new Promise((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        this.off('execution_update', handler);
        reject(new Error(`Timeout waiting for execution ${executionId} completion`));
      }, timeout);

      const handler = (message: WebSocketMessage) => {
        if (message.execution_id === executionId) {
          const update = message.data as ExecutionUpdate;
          if (update.type === 'completion') {
            clearTimeout(timeoutId);
            this.off('execution_update', handler);
            resolve(message);
          }
        }
      };

      this.on('execution_update', handler);
    });
  }

  // Get subscriptions
  getSubscriptions(): string[] {
    return Array.from(this.subscriptions);
  }

  getClientId(): string {
    return this.clientId;
  }
}

// Create singleton instance
export const wsClient = new WebSocketClient();
export default WebSocketClient;