import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 60000, // 60s — pipeline can take 4-8 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred';
    console.error('[ClearMind API]', message);
    return Promise.reject(error);
  }
);

export interface AnalyzeRequest {
  query: string;
  enable_recursive_check?: boolean;
}

export interface BiasDetail {
  bias_type: string;
  confidence: number;
  evidence: string;
  detection_method: string;
  severity: string;
}

export interface BiasReport {
  biases_detected: BiasDetail[];
  overall_bias_score: number;
  is_biased: boolean;
  classifier_available: boolean;
}

export interface StepUpdate {
  step: string;
  status: string;
  data?: Record<string, unknown>;
  timestamp: string;
}

export interface AnalyzeResponse {
  query: string;
  base_answer: string;
  cot_trace: string;
  bias_report: BiasReport;
  corrected_answer: string | null;
  correction_strategy: string | null;
  residual_bias_report: BiasReport | null;
  semantic_similarity: number | null;
  pipeline_steps: StepUpdate[];
  processing_time_ms: number;
  created_at: string;
}

export interface HistoryRecord {
  id: number;
  query: string;
  base_answer: string;
  corrected_answer: string | null;
  biases_detected: string[];
  overall_bias_score: number;
  semantic_similarity: number | null;
  processing_time_ms: number;
  created_at: string;
}

export interface MetricsResponse {
  total_queries: number;
  biased_queries: number;
  bias_rate: number;
  avg_processing_time_ms: number;
  bias_type_frequency: Record<string, number>;
  avg_semantic_similarity: number | null;
  avg_bias_score: number;
}

export const api = {
  analyze: (data: AnalyzeRequest) =>
    apiClient.post<AnalyzeResponse>('/analyze', data),

  getHistory: (limit = 50, offset = 0) =>
    apiClient.get<HistoryRecord[]>('/history', { params: { limit, offset } }),

  getMetrics: () =>
    apiClient.get<MetricsResponse>('/metrics'),
};

export default apiClient;
