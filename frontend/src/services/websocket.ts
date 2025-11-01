import { io, Socket } from 'socket.io-client';

export interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp?: string;
}

export interface WebSocketEventHandlers {
  onConnect?: () => void;
  onDisconnect?: () => void;
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: any) => void;
  onAgentMessage?: (message: WebSocketMessage) => void;
  onExecutionUpdate?: (message: WebSocketMessage) => void;
  onFileUpdate?: (message: WebSocketMessage) => void;
  onExecutionStart?: (message: WebSocketMessage) => void;
  onExecutionComplete?: (message: WebSocketMessage) => void;
  onStageStart?: (message: WebSocketMessage) => void;
  onFileCreated?: (message: WebSocketMessage) => void;
  onWorkflowError?: (message: WebSocketMessage) => void;
}

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private handlers: WebSocketEventHandlers = {};

  constructor() {
    this.connect = this.connect.bind(this);
    this.disconnect = this.disconnect.bind(this);
    this.sendMessage = this.sendMessage.bind(this);
    this.setHandlers = this.setHandlers.bind(this);
  }

  connect(token?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = import.meta.env.VITE_WS_URL || 'http://localhost:8000';

        // Create socket with authentication
        this.socket = io(wsUrl, {
          auth: token ? { token } : undefined,
          transports: ['websocket', 'polling'],
          timeout: 5000,
          forceNew: true,
        });

        // Connection event handlers
        this.socket.on('connect', () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          this.handlers.onConnect?.();
          resolve();
        });

        this.socket.on('disconnect', (reason: string) => {
          console.log('WebSocket disconnected:', reason);
          this.handlers.onDisconnect?.();

          // Attempt reconnection if not manually disconnected
          if (reason === 'io server disconnect' || reason === 'io client disconnect') {
            this.attemptReconnect();
          }
        });

        this.socket.on('connect_error', (error: any) => {
          console.error('WebSocket connection error:', error);
          this.handlers.onError?.(error);
          reject(error);
        });

        // Message event handlers
        this.socket.on('message', (message: WebSocketMessage) => {
          console.log('Received message:', message);
          this.handlers.onMessage?.(message);
        });

        this.socket.on('agent_message', (message: WebSocketMessage) => {
          console.log('Agent message:', message);
          this.handlers.onAgentMessage?.(message);
        });

        this.socket.on('execution_update', (message: WebSocketMessage) => {
          console.log('Execution update:', message);
          this.handlers.onExecutionUpdate?.(message);
        });

        this.socket.on('execution_start', (message: WebSocketMessage) => {
          console.log('Execution start:', message);
          this.handlers.onExecutionStart?.(message);
        });

        this.socket.on('execution_complete', (message: WebSocketMessage) => {
          console.log('Execution complete:', message);
          this.handlers.onExecutionComplete?.(message);
        });

        this.socket.on('stage_start', (message: WebSocketMessage) => {
          console.log('Stage start:', message);
          this.handlers.onStageStart?.(message);
        });

        this.socket.on('file_created', (message: WebSocketMessage) => {
          console.log('File created:', message);
          this.handlers.onFileCreated?.(message);
        });

        this.socket.on('error', (message: WebSocketMessage) => {
          console.log('Workflow error:', message);
          this.handlers.onWorkflowError?.(message);
        });

      } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
        reject(error);
      }
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  sendMessage(message: WebSocketMessage): void {
    if (this.socket && this.socket.connected) {
      this.socket.emit('message', message);
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  }

  sendAgentCommand(command: string, data?: any): void {
    this.sendMessage({
      type: 'agent_command',
      data: { command, ...data },
      timestamp: new Date().toISOString(),
    });
  }

  sendExecutionCommand(command: string, executionId: string, data?: any): void {
    this.sendMessage({
      type: 'execution_command',
      data: { command, executionId, ...data },
      timestamp: new Date().toISOString(),
    });
  }

  sendFileOperation(operation: string, filePath: string, data?: any): void {
    this.sendMessage({
      type: 'file_operation',
      data: { operation, filePath, ...data },
      timestamp: new Date().toISOString(),
    });
  }

  setHandlers(handlers: WebSocketEventHandlers): void {
    this.handlers = { ...this.handlers, ...handlers };
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  getConnectionId(): string | null {
    return this.socket?.id || null;
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      if (!this.isConnected()) {
        this.connect();
      }
    }, delay);
  }

  // Utility methods for common operations
  joinProject(projectId: string): void {
    this.sendMessage({
      type: 'join_project',
      data: { projectId },
      timestamp: new Date().toISOString(),
    });
  }

  leaveProject(projectId: string): void {
    this.sendMessage({
      type: 'leave_project',
      data: { projectId },
      timestamp: new Date().toISOString(),
    });
  }

  subscribeToExecution(executionId: string): void {
    this.sendMessage({
      type: 'subscribe_execution',
      data: { executionId },
      timestamp: new Date().toISOString(),
    });
  }

  unsubscribeFromExecution(executionId: string): void {
    this.sendMessage({
      type: 'unsubscribe_execution',
      data: { executionId },
      timestamp: new Date().toISOString(),
    });
  }
}

// Create singleton instance
const websocketService = new WebSocketService();

export default websocketService;
