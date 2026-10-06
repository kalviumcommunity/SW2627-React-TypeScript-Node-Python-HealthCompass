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

// ─── Dashboard ───────────────────────────────────────────────────

export interface DashboardMetrics {
  totalGuidance: number;
  indexedGuidance: number;
  processingGuidance: number;
  failedGuidance: number;
  archivedGuidance: number;
  recentUpdates: number;
  criticalUpdates: number;
  activeAlerts: number;
}

export interface GuidanceSummary {
  id: string;
  title: string;
  category: string;
  version: string;
  authority: string;
  region: string;
  effectiveDate: string;
  status: string;
  indexedAt: string | null;
}

export interface UpdateSummary {
  id: string;
  title: string;
  category: string;
  severity: string;
  previousVersion: string;
  newVersion: string;
  effectiveDate: string;
  publishedAt: string;
  isRead: boolean;
}

export interface CategoryCount {
  category: string;
  count: number;
}

export interface KnowledgeBaseHealth {
  indexed: number;
  processing: number;
  failed: number;
  archived: number;
}

export interface DashboardResponse {
  metrics: DashboardMetrics;
  recentGuidance: GuidanceSummary[];
  recentUpdates: UpdateSummary[];
  categoryCounts: CategoryCount[];
  knowledgeBaseHealth: KnowledgeBaseHealth;
}

export async function getDashboard(): Promise<DashboardResponse> {
  return apiCall<DashboardResponse>('/stats');
}

// ─── Stats (Legacy - deprecated, use getDashboard) ───────────

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

// ============================================================================
// Policy Updates & Versioning API
// ============================================================================

export type Severity = 'Critical' | 'High' | 'Medium' | 'Low';
export type UpdateCategory = 'outbreak' | 'vaccination' | 'ppe' | 'infection_control' | 'general';
export type UpdateStatus = 'published' | 'draft' | 'superseded' | 'archived';

export interface ChangedSection {
  section_name: string;
  previous_content: string;
  new_content: string;
  change_summary?: string;
}

export interface PolicyUpdate {
  id: string;
  document_id: string;
  document_title: string;
  previous_version_id: string;
  new_version_id: string;
  previous_version: string;
  new_version: string;
  category: UpdateCategory;
  severity: Severity;
  status: UpdateStatus;
  title: string;
  summary: string;
  previous_instruction: string;
  new_instruction: string;
  changed_sections: ChangedSection[];
  effective_date?: string;
  published_at: string;
  published_by?: string;
  authority?: string;
  change_reason?: string;
  impact?: string;
  region?: string;
  is_read: boolean;
  created_at: string;
  updated_at: string;
}

export interface UpdateListResponse {
  items: PolicyUpdate[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface DocumentVersion {
  id: string;
  document_id: string;
  version: string;
  title: string;
  content: string;
  source_file?: string;
  effective_date?: string;
  published_date?: string;
  status: string;
  created_at: string;
}

export interface DiffChange {
  type: 'added' | 'removed' | 'unchanged';
  content: string;
  position: number;
}

export interface SectionDiff {
  section_name: string;
  change_summary?: string;
  diff: DiffChange[];
}

export interface UpdateDiffResponse {
  update_id: string;
  document_title: string;
  previous_version: string;
  new_version: string;
  main_diff: DiffChange[];
  section_diffs: SectionDiff[];
  summary: {
    total_changes: number;
    added_count: number;
    removed_count: number;
    unchanged_count: number;
    change_percentage: number;
  };
}

export async function getUpdates(
  params?: {
    category?: UpdateCategory;
    search?: string;
    status?: UpdateStatus;
    page?: number;
    page_size?: number;
  }
): Promise<UpdateListResponse> {
  const queryParams = new URLSearchParams();
  if (params?.category) queryParams.set('category', params.category);
  if (params?.search) queryParams.set('search', params.search);
  if (params?.status) queryParams.set('status', params.status);
  if (params?.page) queryParams.set('page', params.page.toString());
  if (params?.page_size) queryParams.set('page_size', params.page_size.toString());
  
  const queryString = queryParams.toString();
  return apiCall<UpdateListResponse>(`/api/updates${queryString ? `?${queryString}` : ''}`);
}

export async function getUpdateDetail(updateId: string): Promise<PolicyUpdate> {
  return apiCall<PolicyUpdate>(`/api/updates/${updateId}`);
}

export async function getArchivedUpdates(
  params?: { page?: number; page_size?: number }
): Promise<UpdateListResponse> {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.set('page', params.page.toString());
  if (params?.page_size) queryParams.set('page_size', params.page_size.toString());
  
  const queryString = queryParams.toString();
  return apiCall<UpdateListResponse>(`/api/updates/archive${queryString ? `?${queryString}` : ''}`);
}

export async function markUpdateAsRead(updateId: string): Promise<{ status: string; message: string }> {
  return apiCall<{ status: string; message: string }>(`/api/updates/${updateId}/read`, {
    method: 'POST',
  });
}

export async function getUnreadCount(): Promise<{ count: number }> {
  return apiCall<{ count: number }>('/api/updates/unread/count');
}

export async function getDocumentVersion(versionId: string): Promise<DocumentVersion> {
  return apiCall<DocumentVersion>(`/api/versions/${versionId}`);
}

export async function getDocumentVersions(documentId: string): Promise<{
  document_id: string;
  versions: DocumentVersion[];
  total: number;
}> {
  return apiCall<{ document_id: string; versions: DocumentVersion[]; total: number }>(
    `/api/documents/${documentId}/versions`
  );
}

export async function getUpdateDiff(updateId: string): Promise<UpdateDiffResponse> {
  return apiCall<UpdateDiffResponse>(`/api/updates/${updateId}/diff`);
}

// ============================================================================
// Legacy Exports (other pages still use these)
// ============================================================================

export async function getGuidance(): Promise<GuidanceItem[]> {
  return apiCall<GuidanceItem[]>('/guidance');
}

export async function searchGuidance(query: string): Promise<GuidanceItem[]> {
  return apiCall<GuidanceItem[]>(`/guidance/search?query=${encodeURIComponent(query)}`);
}

export async function getAlerts(): Promise<AlertItem[]> {
  return apiCall<AlertItem[]>('/alerts');
}

// Legacy update endpoint for backward compatibility
export async function getLegacyUpdates(): Promise<UpdateItem[]> {
  return apiCall<UpdateItem[]>('/updates');
}

// ─── Saved Guidance ──────────────────────────────────────────────

export interface SavedGuidanceItem {
  id: string;
  document_id?: string;
  title: string;
  topic: string;
  source: string;
  excerpt?: string;
  dateSaved: string;
}

export async function getSavedGuidance(): Promise<SavedGuidanceItem[]> {
  return apiCall<SavedGuidanceItem[]>('/api/saved');
}

export async function saveGuidance(item: Partial<SavedGuidanceItem>): Promise<SavedGuidanceItem> {
  return apiCall<SavedGuidanceItem>('/api/saved', {
    method: 'POST',
    body: JSON.stringify(item),
  });
}

export async function removeSavedGuidance(id: string): Promise<{ success: boolean; id: string }> {
  return apiCall<{ success: boolean; id: string }>(`/api/saved/${id}`, {
    method: 'DELETE',
  });
}

// Re-export types that other pages reference
export type { ApiAskResponse as AskResponse, ApiSourceInfo as SourceInfo };
