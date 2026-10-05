// API client configuration
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const API_BASE_URL = API_URL;

// API response types
export interface AskResponse {
  answer: string;
  sources: SourceInfo[];
  context_tokens: number;
  chunks_used: number;
}

export interface SourceInfo {
  chunk_id: string;
  source: string;
  chunk_index: string;
  rank: number;
  distance: number;
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
}

// Generic API error
export class ApiError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

// Helper function for API calls
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

// API functions
export async function askHealthCompass(question: string): Promise<AskResponse> {
  return apiCall<AskResponse>('/ask', {
    method: 'POST',
    body: JSON.stringify({ question }),
  });
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
