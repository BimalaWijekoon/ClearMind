import { useState, useCallback } from 'react';
import { api } from '../api/client';
import type { AnalyzeResponse, HistoryRecord, MetricsResponse } from '../api/client';

interface UseBiasAnalysisReturn {
  analyzeResult: AnalyzeResponse | null;
  history: HistoryRecord[];
  metrics: MetricsResponse | null;
  isLoading: boolean;
  error: string | null;
  analyze: (query: string) => Promise<void>;
  fetchHistory: () => Promise<void>;
  fetchMetrics: () => Promise<void>;
}

export function useBiasAnalysis(): UseBiasAnalysisReturn {
  const [analyzeResult, setAnalyzeResult] = useState<AnalyzeResponse | null>(null);
  const [history, setHistory] = useState<HistoryRecord[]>([]);
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyze = useCallback(async (query: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const { data } = await api.analyze({ query });
      setAnalyzeResult(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Analysis failed';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchHistory = useCallback(async () => {
    try {
      const { data } = await api.getHistory();
      setHistory(data);
    } catch (err: unknown) {
      console.error('Failed to fetch history:', err);
    }
  }, []);

  const fetchMetrics = useCallback(async () => {
    try {
      const { data } = await api.getMetrics();
      setMetrics(data);
    } catch (err: unknown) {
      console.error('Failed to fetch metrics:', err);
    }
  }, []);

  return {
    analyzeResult, history, metrics,
    isLoading, error,
    analyze, fetchHistory, fetchMetrics,
  };
}
