// API client configuration
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const API_BASE_URL = API_URL;

export interface CitationInfo {
  index: number;
  chunk_id: string;
  source: string;
  section?: string | null;
  snippet: string;
  distance: number;
}

export interface SourceInfo {
  chunk_id: string;
  source: string;
  chunk_index: string;
  rank: number;
  distance: number;
}

export interface AskResponse {
  answer: string;
  citations: CitationInfo[];
  sources: SourceInfo[];
  context_tokens: number;
  chunks_used: number;
  chunks_retrieved?: number;
  is_refusal?: boolean;
  faithfulness_score?: number;
  latency_ms?: number;
  cached?: boolean;
}

export interface GuidanceItem {
  id: string;
  title: string;
  topic: string;
  description: string;
  source: string;
  last_updated: string;
}

export interface AlertItem {
  id: string;
  severity: string;
  topic: string;
  location: string | null;
  date: string;
  description: string;
  status: string;
}

export interface UpdateItem {
  id: string;
  title: string;
  category: string;
  date: string;
  summary: string;
  importance: string;
}

export interface Stats {
  active_alerts: number;
  new_guidance: number;
  policy_updates: number;
  saved_guidance: number;
  total_queries_served?: number;
  cache_hits?: number;
  cache_misses?: number;
  avg_latency_ms?: number;
}

export interface UsageMetrics {
  total_requests: number;
  total_tokens: number;
  avg_latency_ms: number;
  cache_hits: number;
  cache_misses: number;
  cache_hit_rate: number;
}

export interface UploadResponse {
  filename: string;
  chunks_indexed: number;
  status: string;
  message: string;
}

export class ApiError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function apiCall<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.text();
    throw new ApiError(error || 'API request failed', response.status);
  }

  return response.json();
}

export interface AskOptions {
  history?: Array<{ role: string; content: string }>;
  metadata_filter?: Record<string, string | number | boolean>;
  keyword_weight?: number;
  candidate_k?: number;
  top_k?: number;
  enable_rerank?: boolean;
}

export async function askHealthCompass(
  question: string,
  options: AskOptions = {}
): Promise<AskResponse> {
  return apiCall<AskResponse>('/ask', {
    method: 'POST',
    body: JSON.stringify({ question, ...options }),
  });
}

export async function askHealthCompassStream(
  question: string,
  onToken: (token: string) => void,
  onComplete: () => void,
  onError: (err: Error) => void,
  options: AskOptions = {}
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/ask/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question, ...options }),
    });

    if (!response.ok || !response.body) {
      throw new Error(`Streaming failed: HTTP ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const jsonStr = line.slice(6).trim();
          if (jsonStr) {
            try {
              const data = JSON.parse(jsonStr);
              if (data.token) {
                onToken(data.token);
              }
              if (data.done) {
                onComplete();
                return;
              }
              if (data.error) {
                onError(new Error(data.error));
                return;
              }
            } catch {
              // Ignore partial parse errors
            }
          }
        }
      }
    }
    onComplete();
  } catch (err: any) {
    onError(err);
  }
}

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.text();
    throw new ApiError(error || 'Upload failed', response.status);
  }

  return response.json();
}

export async function getGuidance(): Promise<GuidanceItem[]> {
  return apiCall<GuidanceItem[]>('/guidance');
}

export async function searchGuidance(query: string): Promise<GuidanceItem[]> {
  return apiCall<GuidanceItem[]>(`/guidance/search?query=${encodeURIComponent(query)}`);
}

export async function getAlerts(): Promise<AlertItem[]> {
  return apiCall<AlertItem[]>('/alerts');
}

export async function getUpdates(): Promise<UpdateItem[]> {
  return apiCall<UpdateItem[]>('/updates');
}

export async function getStats(): Promise<Stats> {
  return apiCall<Stats>('/stats');
}

export async function getUsageMetrics(): Promise<UsageMetrics> {
  return apiCall<UsageMetrics>('/stats/usage');
}
