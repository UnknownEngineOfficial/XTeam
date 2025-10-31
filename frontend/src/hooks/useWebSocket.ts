import { useEffect, useState, useCallback } from 'react';
import websocketService, { WebSocketMessage, WebSocketEventHandlers } from '../services/websocket';

interface UseWebSocketOptions {
  autoConnect?: boolean;
  token?: string;
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

interface UseWebSocketReturn {
  isConnected: boolean;
  connectionId: string | null;
  connect: () => Promise<void>;
  disconnect: () => void;
  sendMessage: (message: WebSocketMessage) => void;
  sendAgentCommand: (command: string, data?: any) => void;
  sendExecutionCommand: (command: string, executionId: string, data?: any) => void;
  sendFileOperation: (operation: string, filePath: string, data?: any) => void;
  joinProject: (projectId: string) => void;
  leaveProject: (projectId: string) => void;
  subscribeToExecution: (executionId: string) => void;
  unsubscribeFromExecution: (executionId: string) => void;
}

export const useWebSocket = (options: UseWebSocketOptions = {}): UseWebSocketReturn => {
  const {
    autoConnect = false,
    token,
    onConnect,
    onDisconnect,
    onMessage,
    onError,
    onAgentMessage,
    onExecutionUpdate,
    onFileUpdate,
    onExecutionStart,
    onExecutionComplete,
    onStageStart,
    onFileCreated,
    onWorkflowError,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [connectionId, setConnectionId] = useState<string | null>(null);

  // Update connection state
  const updateConnectionState = useCallback(() => {
    setIsConnected(websocketService.isConnected());
    setConnectionId(websocketService.getConnectionId());
  }, []);

  // Set up event handlers
  useEffect(() => {
    const handlers: WebSocketEventHandlers = {
      onConnect: () => {
        updateConnectionState();
        onConnect?.();
      },
      onDisconnect: () => {
        updateConnectionState();
        onDisconnect?.();
      },
      onMessage,
      onError,
      onAgentMessage,
      onExecutionUpdate,
      onFileUpdate,
      onExecutionStart,
      onExecutionComplete,
      onStageStart,
      onFileCreated,
      onWorkflowError,
    };

    websocketService.setHandlers(handlers);

    // Auto-connect if requested
    if (autoConnect) {
      connect();
    }

    // Update initial state
    updateConnectionState();

    // Cleanup on unmount
    return () => {
      if (!autoConnect) {
        websocketService.disconnect();
      }
    };
  }, [
    autoConnect,
    token,
    onConnect,
    onDisconnect,
    onMessage,
    onError,
    onAgentMessage,
    onExecutionUpdate,
    onFileUpdate,
    updateConnectionState,
  ]);

  const connect = useCallback(async () => {
    try {
      await websocketService.connect(token);
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      onError?.(error);
    }
  }, [token, onError]);

  const disconnect = useCallback(() => {
    websocketService.disconnect();
  }, []);

  const sendMessage = useCallback((message: WebSocketMessage) => {
    websocketService.sendMessage(message);
  }, []);

  const sendAgentCommand = useCallback((command: string, data?: any) => {
    websocketService.sendAgentCommand(command, data);
  }, []);

  const sendExecutionCommand = useCallback((command: string, executionId: string, data?: any) => {
    websocketService.sendExecutionCommand(command, executionId, data);
  }, []);

  const sendFileOperation = useCallback((operation: string, filePath: string, data?: any) => {
    websocketService.sendFileOperation(operation, filePath, data);
  }, []);

  const joinProject = useCallback((projectId: string) => {
    websocketService.joinProject(projectId);
  }, []);

  const leaveProject = useCallback((projectId: string) => {
    websocketService.leaveProject(projectId);
  }, []);

  const subscribeToExecution = useCallback((executionId: string) => {
    websocketService.subscribeToExecution(executionId);
  }, []);

  const unsubscribeFromExecution = useCallback((executionId: string) => {
    websocketService.unsubscribeFromExecution(executionId);
  }, []);

  return {
    isConnected,
    connectionId,
    connect,
    disconnect,
    sendMessage,
    sendAgentCommand,
    sendExecutionCommand,
    sendFileOperation,
    joinProject,
    leaveProject,
    subscribeToExecution,
    unsubscribeFromExecution,
  };
};

export default useWebSocket;
