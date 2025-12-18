import { useState, useEffect, useRef, useCallback } from 'react';

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
const RECONNECT_INTERVAL = 5000; // 5 seconds

/**
 * Custom hook for WebSocket connection with auto-reconnect
 * @param {string} path - WebSocket path (e.g., '/ws' or '/ws/nurse/{sessionId}')
 * @param {Object} options - Configuration options
 * @param {Function} options.onMessage - Callback for incoming messages
 * @param {Function} options.onConnect - Callback when connected
 * @param {Function} options.onDisconnect - Callback when disconnected
 * @param {Function} options.onError - Callback for errors
 * @param {boolean} options.autoConnect - Auto-connect on mount (default: true)
 * @param {boolean} options.autoReconnect - Auto-reconnect on disconnect (default: true)
 * @returns {Object} WebSocket state and methods
 */
export const useWebSocket = (path, options = {}) => {
  const {
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    autoConnect = true,
    autoReconnect = true,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [connectionAttempts, setConnectionAttempts] = useState(0);
  
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const shouldReconnectRef = useRef(autoReconnect);
  const isManualCloseRef = useRef(false);

  // Clear reconnect timeout
  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  // Connect to WebSocket - use regular function to avoid circular dependency
  const connect = useCallback(() => {
    // Close existing connection
    if (wsRef.current) {
      isManualCloseRef.current = true;
      wsRef.current.close();
      wsRef.current = null;
    }

    const wsUrl = `${WS_BASE_URL}${path}`;
    console.log(`[WebSocket] Connecting to ${wsUrl}...`);

    const attemptConnection = () => {
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;
        isManualCloseRef.current = false;

        ws.onopen = () => {
          console.log('[WebSocket] Connected');
          setIsConnected(true);
          setConnectionAttempts(0);
          clearReconnectTimeout();
          
          if (onConnect) {
            onConnect();
          }
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('[WebSocket] Message received:', data);
            setLastMessage(data);
            
            if (onMessage) {
              onMessage(data);
            }
          } catch (error) {
            console.error('[WebSocket] Failed to parse message:', error);
          }
        };

        ws.onerror = (error) => {
          console.error('[WebSocket] Error:', error);
          
          if (onError) {
            onError(error);
          }
        };

        ws.onclose = (event) => {
          console.log('[WebSocket] Disconnected', event.code, event.reason);
          setIsConnected(false);
          wsRef.current = null;

          if (onDisconnect) {
            onDisconnect(event);
          }

          // Auto-reconnect if not manually closed
          if (shouldReconnectRef.current && !isManualCloseRef.current) {
            setConnectionAttempts((prev) => prev + 1);
            console.log(`[WebSocket] Attempting to reconnect in ${RECONNECT_INTERVAL}ms...`);
            
            reconnectTimeoutRef.current = setTimeout(attemptConnection, RECONNECT_INTERVAL);
          }
        };
      } catch (error) {
        console.error('[WebSocket] Connection error:', error);
        
        if (onError) {
          onError(error);
        }

        // Retry connection
        if (shouldReconnectRef.current) {
          setConnectionAttempts((prev) => prev + 1);
          reconnectTimeoutRef.current = setTimeout(attemptConnection, RECONNECT_INTERVAL);
        }
      }
    };

    attemptConnection();
  }, [path, onMessage, onConnect, onDisconnect, onError, clearReconnectTimeout]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    console.log('[WebSocket] Manual disconnect');
    shouldReconnectRef.current = false;
    isManualCloseRef.current = true;
    clearReconnectTimeout();
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
  }, [clearReconnectTimeout]);

  // Send message through WebSocket
  const sendMessage = useCallback((data) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const message = typeof data === 'string' ? data : JSON.stringify(data);
      wsRef.current.send(message);
      console.log('[WebSocket] Message sent:', data);
      return true;
    } else {
      console.warn('[WebSocket] Cannot send message - not connected');
      return false;
    }
  }, []);

  // Reconnect manually
  const reconnect = useCallback(() => {
    console.log('[WebSocket] Manual reconnect');
    shouldReconnectRef.current = true;
    connect();
  }, [connect]);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      shouldReconnectRef.current = false;
      clearReconnectTimeout();
      
      if (wsRef.current) {
        isManualCloseRef.current = true;
        wsRef.current.close();
      }
    };
  }, [autoConnect, connect, clearReconnectTimeout]);

  return {
    isConnected,
    lastMessage,
    connectionAttempts,
    connect,
    disconnect,
    reconnect,
    sendMessage,
  };
};

/**
 * Hook for main dashboard WebSocket connection
 * @param {Object} handlers - Event handlers
 * @returns {Object} WebSocket state and methods
 */
export const useDashboardWebSocket = (handlers = {}) => {
  return useWebSocket('/ws', {
    onMessage: (data) => {
      // Handle different event types
      const { event } = data;
      
      switch (event) {
        case 'patient_admitted':
          handlers.onPatientAdmitted?.(data.patient);
          break;
        case 'patient_discharged':
          handlers.onPatientDischarged?.(data.patient);
          break;
        default:
          // Sensor data or alarm updates
          handlers.onSensorData?.(data);
          break;
      }
      
      // Call general message handler
      handlers.onMessage?.(data);
    },
    onConnect: handlers.onConnect,
    onDisconnect: handlers.onDisconnect,
    onError: handlers.onError,
  });
};

/**
 * Hook for nurse proximity alert WebSocket connection
 * @param {string} sessionId - Nurse session ID
 * @param {Object} handlers - Event handlers
 * @returns {Object} WebSocket state and methods
 */
export const useNurseWebSocket = (sessionId, handlers = {}) => {
  return useWebSocket(`/ws/nurse/${sessionId}`, {
    onMessage: (data) => {
      // Handle vibration alerts
      if (data.type === 'VIBRATION_ALERT') {
        handlers.onVibrationAlert?.(data);
      }
      
      // Call general message handler
      handlers.onMessage?.(data);
    },
    onConnect: handlers.onConnect,
    onDisconnect: handlers.onDisconnect,
    onError: handlers.onError,
    autoConnect: !!sessionId, // Only connect if sessionId exists
  });
};

export default useWebSocket;
