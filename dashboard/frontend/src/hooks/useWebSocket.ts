import { useEffect, useRef } from 'react';
import { WebSocketMessage } from '../types';

export const useWebSocket = (
  url: string,
  onMessage: (message: WebSocketMessage) => void
) => {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 10;
  const isClosingRef = useRef(false);

  useEffect(() => {
    let shouldReconnect = true;

    const connect = () => {
      if (!shouldReconnect || isClosingRef.current) return;

      try {
        console.log(`WebSocket connecting to ${url}... (attempt ${reconnectAttemptsRef.current + 1})`);
        const ws = new WebSocket(url);
        wsRef.current = ws;

        ws.onopen = () => {
          console.log('WebSocket connected');
          reconnectAttemptsRef.current = 0; // Reset attempts on successful connection
          if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
          }
        };

        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            if (message.type === 'error') {
              console.error('Server error:', message.message);
            } else {
              onMessage(message);
            }
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };

        ws.onclose = (event) => {
          if (!isClosingRef.current) {
            console.log(`WebSocket disconnected (code: ${event.code}, reason: ${event.reason})`);
            wsRef.current = null;

            // Implement exponential backoff for reconnection
            if (reconnectAttemptsRef.current < maxReconnectAttempts && shouldReconnect) {
              reconnectAttemptsRef.current++;
              const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
              console.log(`Reconnecting in ${delay / 1000} seconds...`);
              reconnectTimeoutRef.current = setTimeout(connect, delay);
            } else {
              console.error('Max reconnection attempts reached. Please refresh the page.');
            }
          }
        };
      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        // Retry connection with exponential backoff
        if (reconnectAttemptsRef.current < maxReconnectAttempts && shouldReconnect) {
          reconnectAttemptsRef.current++;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
          reconnectTimeoutRef.current = setTimeout(connect, delay);
        }
      }
    };

    connect();

    // Cleanup
    return () => {
      shouldReconnect = false;
      isClosingRef.current = true;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close(1000, 'Component unmounting');
      }
    };
  }, [url]); // Remove onMessage from dependencies to prevent reconnects

  return wsRef.current;
};