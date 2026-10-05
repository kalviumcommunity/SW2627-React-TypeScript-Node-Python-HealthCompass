/**
 * HealthCompass API Client
 *
 * All communication with the FastAPI backend goes through this module.
 * No API keys, RAG logic, or embedding calls belong here —
 * everything is server-side.
 */

import type {
  ApiAskResponse,
  ApiHealthCheck,
  ApiSourceInfo,
  RagAnswer,
  RagSource,
} from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ─── Error Class ─────────────────────────────────────────────────

export class ApiError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

// ─── Generic Fetch Helper ────────────────────────────────────────

async function apiCall<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_URL}${endpoint}`;

  let response: Response;
  try {
    response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });
  } catch {
    throw new ApiError(
      'Unable to reach the HealthCompass server. Please check that the backend is running.',
    );
  }

  if (!response.ok) {
    let errorMessage = 'API request failed';
    try {
      const body = await response.json();
      errorMessage = body.detail || body.message || JSON.stringify(body);
    } catch {
      errorMessage = await response.text();
    }
    throw new ApiError(errorMessage, response.status);
  }

  return response.json();
}

// ─── Stats ───────────────────────────────────────────────────────

export interface Stats {
  active_alerts: number;
  active_alerts_subtitle: string;
  new_guidance: number;
  new_guidance_subtitle: string;
  policy_updates: number;
  policy_updates_subtitle: string;
  saved_guidance: number;
  saved_guidance_subtitle: string;
}

export async function getStats(): Promise<Stats> {
  return apiCall<Stats>('/stats');
}

// ─── Health Check ────────────────────────────────────────────────

export async function getHealthCheck(): Promise<ApiHealthCheck> {
  return apiCall<ApiHealthCheck>('/health');
}

// ─── Ask HealthCompass (RAG) ─────────────────────────────────────

function relevanceLabel(distance: number): string {
  const score = 1 - distance;
  if (score >= 0.85) return 'High relevance';
  if (score >= 0.7) return 'Relevant match';
  if (score >= 0.5) return 'Partial match';
  return 'Low relevance';
}

function formatSourceTitle(source: string): string {
  // Convert filenames like "outbreak_response.txt" → "Outbreak Response"
  return source
    .replace(/\.[^/.]+$/, '')              // remove extension
    .replace(/[_-]/g, ' ')                 // replace separators
    .replace(/\b\w/g, (c) => c.toUpperCase()); // title case
}

function mapSource(s: ApiSourceInfo): RagSource {
  return {
    chunkId: s.chunk_id,
    title: formatSourceTitle(s.source),
    source: s.source,
    chunkIndex: s.chunk_index,
    rank: s.rank,
    distance: s.distance,
    excerpt: s.excerpt || '',
    relevanceLabel: relevanceLabel(s.distance),
  };
}

export async function askHealthCompass(question: string): Promise<RagAnswer> {
  const raw = await apiCall<ApiAskResponse>('/ask', {
    method: 'POST',
    body: JSON.stringify({ question }),
  });

  // Fetch provider info (best-effort, don't block answer)
  let provider = '';
  let embeddingProvider = '';
  try {
    const health = await getHealthCheck();
    provider = health.chat_provider;
    embeddingProvider = health.embedding_provider;
  } catch {
    // Silently ignore — not critical
  }

  return {
    answer: raw.answer,
    sources: raw.sources.map(mapSource),
    query: question,
    metadata: {
      contextTokens: raw.context_tokens,
      chunksUsed: raw.chunks_used,
      provider,
      embeddingProvider,
    },
  };
}

// ─── Legacy Exports (other pages still use these) ────────────────

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

// Re-export types that other pages reference
export type { ApiAskResponse as AskResponse, ApiSourceInfo as SourceInfo };
