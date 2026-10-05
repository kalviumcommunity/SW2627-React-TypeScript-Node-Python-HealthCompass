/**
 * HealthCompass Frontend Type Definitions
 *
 * Centralized types for all frontend data models.
 * These types mirror backend response shapes and provide
 * structure for demo/static data used before API integration.
 */

// ─── Dashboard Types ─────────────────────────────────────────────

export interface DashboardMetric {
  id: string;
  label: string;
  value: number;
  icon: string;
  subtitle: string;
  href: string;
}

export interface Directive {
  id: string;
  status: 'active' | 'pending' | 'expired';
  title: string;
  authority: string;
  effectiveDate: string;
  category: string;
  summary?: string;
  version?: string;
}

export interface ActiveDirective extends Directive {
  region: string;
  description: string;
  actions: DirectiveAction[];
}

export interface DirectiveAction {
  label: string;
  href: string;
}

export interface DistrictStatus {
  name: string;
  metrics: DistrictMetric[];
}

export interface DistrictMetric {
  label: string;
  value: string | number;
  trend?: 'up' | 'down' | 'stable';
}

export interface GuidanceTopic {
  id: string;
  icon: string;
  title: string;
  description: string;
  href: string;
}

export interface ActivityItem {
  id: string;
  icon: string;
  description: string;
  timestamp: string;
  category: string;
}

export interface CaseTrend {
  day: string;
  cases: number;
  responses: number;
}

export interface UserProfile {
  name: string;
  initials: string;
  role: string;
  region: string;
  department: string;
}

// ─── RAG / Ask Types ─────────────────────────────────────────────

export interface RagSource {
  chunkId: string;
  title: string;
  source: string;
  chunkIndex: string;
  rank: number;
  distance: number;
  excerpt: string;
  relevanceLabel: string;
}

export interface RagAnswer {
  answer: string;
  sources: RagSource[];
  query: string;
  metadata: {
    contextTokens: number;
    chunksUsed: number;
    provider: string;
    embeddingProvider: string;
  };
}

export interface ConversationEntry {
  id: string;
  question: string;
  answer: RagAnswer | null;
  timestamp: string;
  status: 'loading' | 'success' | 'error' | 'no-results';
  errorMessage?: string;
}

// ─── API Response Types (mirror backend) ─────────────────────────

export interface ApiAskResponse {
  answer: string;
  sources: ApiSourceInfo[];
  context_tokens: number;
  chunks_used: number;
}

export interface ApiSourceInfo {
  chunk_id: string;
  source: string;
  chunk_index: string;
  rank: number;
  distance: number;
  excerpt: string;
}

export interface ApiStats {
  active_alerts: number;
  new_guidance: number;
  policy_updates: number;
  saved_guidance: number;
}

export interface ApiHealthCheck {
  status: string;
  chat_provider: string;
  embedding_provider: string;
  chat_model: string;
  embedding_model: string;
}
