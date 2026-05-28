import { useState, useRef, useCallback, useEffect } from 'react';
import type { StepUpdate, AnalyzeResponse } from '../api/client';

interface UseWebSocketReturn {
  steps: StepUpdate[];
  result: AnalyzeResponse | null;
  error: string | null;
  isConnected: boolean;
  isProcessing: boolean;
  sendQuery: (query: string, enableRecursiveCheck?: boolean) => void;
  reset: () => void;
}

export function useWebSocket(): UseWebSocketReturn {
  const [steps, setSteps] = useState<StepUpdate[]>([]);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const reset = useCallback(() => {
    setSteps([]);
    setResult(null);
    setError(null);
    setIsProcessing(false);
  }, []);

  const sendQuery = useCallback((query: string, enableRecursiveCheck = true) => {
    reset();
    setIsProcessing(true);

    // Determine WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/analyze`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      ws.send(JSON.stringify({
        query,
        enable_recursive_check: enableRecursiveCheck,
      }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.error) {
          setError(data.error);
          setIsProcessing(false);
          return;
        }

        if (data.type === 'result') {
          setResult(data.data as AnalyzeResponse);
          setIsProcessing(false);
        } else {
          // It's a step update
          setSteps((prev) => [...prev, data as StepUpdate]);
        }
      } catch {
        console.error('Failed to parse WebSocket message');
      }
    };

    ws.onerror = () => {
      setError('WebSocket connection failed. Is the backend running?');
      setIsProcessing(false);
    };

    ws.onclose = () => {
      setIsConnected(false);
    };
  }, [reset]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return { steps, result, error, isConnected, isProcessing, sendQuery, reset };
}
