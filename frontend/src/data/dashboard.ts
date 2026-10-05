/**
 * Dashboard Data Layer
 *
 * Centralized demo data for the Dashboard page.
 * All values are defined here so they can later be replaced
 * by real API calls without touching component JSX.
 */

import type {
  ActiveDirective,
  ActivityItem,
  CaseTrend,
  Directive,
  DistrictStatus,
  GuidanceTopic,
  UserProfile,
} from '../types';

// ─── User Profile ────────────────────────────────────────────────

export const currentUser: UserProfile = {
  name: 'Sarah Jenkins',
  initials: 'SJ',
  role: 'Field Medical Officer',
  region: 'District A',
  department: 'Field Operations',
};

// ─── Active Directive ────────────────────────────────────────────

export const activeDirective: ActiveDirective = {
  id: 'dir-001',
  status: 'active',
  region: 'District A',
  title: 'Outbreak Protocol v4.2 in Effect',
  authority: 'National Public Health Authority',
  effectiveDate: 'Aug 12, 2026',
  category: 'Outbreak Response',
  version: 'v4.2',
  description:
    'Updated isolation and testing protocols for acute respiratory cases. All field units must follow the current PPE tier requirements.',
  summary:
    'Updated isolation and testing protocols for acute respiratory cases. All field units must follow the current PPE tier requirements.',
  actions: [
    { label: 'Review Updates', href: '/updates' },
    { label: 'View Protocol', href: '/guidance' },
  ],
};

// ─── Field Directives ────────────────────────────────────────────

export const fieldDirectives: Directive[] = [
  {
    id: 'fd-001',
    status: 'active',
    title: 'Outbreak Response Guideline',
    authority: 'National Public Health Authority',
    effectiveDate: 'Aug 12, 2026',
    category: 'Outbreak Response',
  },
  {
    id: 'fd-002',
    status: 'active',
    title: 'Pediatric & Adult Vaccination Protocol',
    authority: 'District Health Office',
    effectiveDate: 'Aug 10, 2026',
    category: 'Vaccination',
  },
  {
    id: 'fd-003',
    status: 'active',
    title: 'Contact Tracing & Surveillance SOP',
    authority: 'National Public Health Authority',
    effectiveDate: 'Aug 8, 2026',
    category: 'Surveillance',
  },
];

// ─── District Status ─────────────────────────────────────────────

export const districtStatus: DistrictStatus = {
  name: 'District A',
  metrics: [
    { label: 'Active Mobile Units', value: 24, trend: 'stable' },
    { label: 'Total Cases', value: 312, trend: 'up' },
    { label: 'Protocol Adoption', value: '78%', trend: 'up' },
    { label: 'Current PPE Tier', value: 'Tier 2', trend: 'stable' },
  ],
};

// ─── Quick Topics ────────────────────────────────────────────────

export const quickTopics: GuidanceTopic[] = [
  {
    id: 'qt-001',
    icon: 'ClipboardList',
    title: 'Vaccination Protocols',
    description: 'Dosing schedules, priority groups, and contraindications',
    href: '/ask',
  },
  {
    id: 'qt-002',
    icon: 'Shield',
    title: 'PPE & Infection Control',
    description: 'Tier requirements, donning/doffing, and disposal',
    href: '/ask',
  },
  {
    id: 'qt-003',
    icon: 'AlertTriangle',
    title: 'Emergency SOPs',
    description: 'Rapid response procedures and escalation protocols',
    href: '/ask',
  },
  {
    id: 'qt-004',
    icon: 'Activity',
    title: 'Triage & Intake Rules',
    description: 'Patient classification and initial assessment criteria',
    href: '/ask',
  },
];

// ─── Suggested Questions ─────────────────────────────────────────

export const suggestedQuestions = [
  'Isolation protocol',
  'Vaccination interval',
  'District PPE rules',
];

// ─── Cases Trend Data ────────────────────────────────────────────

export const casesTrend: CaseTrend[] = [
  { day: 'Mon', cases: 198, responses: 180 },
  { day: 'Tue', cases: 225, responses: 210 },
  { day: 'Wed', cases: 248, responses: 230 },
  { day: 'Thu', cases: 270, responses: 255 },
  { day: 'Fri', cases: 290, responses: 275 },
  { day: 'Sat', cases: 305, responses: 290 },
  { day: 'Sun', cases: 312, responses: 298 },
];

// ─── Recent Activity ─────────────────────────────────────────────

export const recentActivity: ActivityItem[] = [
  {
    id: 'act-001',
    icon: 'FileText',
    description: 'Outbreak Response Guideline v4.2 added',
    timestamp: '2 hours ago',
    category: 'Document',
  },
  {
    id: 'act-002',
    icon: 'RefreshCw',
    description: 'Vaccination protocol updated to v3.1',
    timestamp: '5 hours ago',
    category: 'Update',
  },
  {
    id: 'act-003',
    icon: 'Bookmark',
    description: 'Sarah saved PPE Infection Control guide',
    timestamp: '1 day ago',
    category: 'Saved',
  },
  {
    id: 'act-004',
    icon: 'AlertTriangle',
    description: 'New respiratory illness alert for District A',
    timestamp: '1 day ago',
    category: 'Alert',
  },
];
