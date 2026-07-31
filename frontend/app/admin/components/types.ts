/**
 * Shared TypeScript interfaces and types for the Admin Dashboard redesign.
 *
 * All section components and the AdminDashboardProvider consume types from this
 * module to ensure a single source of truth across the feature.
 */

// Re-export API response types used by the dashboard context
export type {
  ActiveSessionsResponse,
  CapstoneSubmissionsResponse,
  ModuleHealthResponse,
  RegistryStatusResponse,
} from '@/lib/api';

// ---------------------------------------------------------------------------
// Analytics data (matches the shape returned by apiClient.getAnalytics())
// ---------------------------------------------------------------------------

export interface AnalyticsData {
  total_registered_users: number;
  active_sessions: number;
  users_with_progress: number;
  users_completed_all: number;
  total_completions: number;
  average_completion_rate: number;
  engagement_rate: number;
  active_learners_7d: number;
  total_capstone_submissions: number;
  registration_timeline: Array<{ date: string; count: number }>;
  completion_by_user: Array<{
    user_id: string;
    username: string;
    completed: number;
    percentage: number;
  }>;
  badge_stats?: {
    total_badges_earned: number;
    unique_users_with_badges: number;
    badge_distribution: Array<{
      badge_id: string;
      badge_title: string;
      count: number;
    }>;
  };
  quiz_stats?: {
    total_quiz_attempts: number;
    average_score: number;
    perfect_scores: number;
    quiz_performance: Array<{
      module_id: string;
      attempts: number;
      avg_score: number;
    }>;
  };
}

// ---------------------------------------------------------------------------
// AdminDashboardProvider context value
// ---------------------------------------------------------------------------

export interface AttentionCounts {
  pendingCapstones: number;
  pendingTestimonials: number;
  moduleHealthIssues: number;
  registryIssues: number;
}

export interface KpiMetric {
  id: string;
  label: string;
  value: number | string;
  sublabel?: string;
  onClick?: () => void;
  visible: boolean;
}

export interface AdminDashboardContextValue {
  // Raw API data
  analytics: AnalyticsData | null;
  activeSessions: import('@/lib/api').ActiveSessionsResponse | null;
  submissions: import('@/lib/api').CapstoneSubmissionsResponse | null;
  moduleHealth: import('@/lib/api').ModuleHealthResponse | null;
  registryStatus: import('@/lib/api').RegistryStatusResponse | null;

  // Derived data
  attentionCounts: AttentionCounts;
  kpiMetrics: KpiMetric[];

  // State flags
  isLoading: boolean;
  errors: Record<string, string | null>;

  // Sessions modal state
  sessionsModalOpen: boolean;

  // Actions
  refetchAll: () => void;
  refetchAnalytics: () => void;
  openSessionsModal: () => void;
  closeSessionsModal: () => void;
}

// ---------------------------------------------------------------------------
// KpiCard component props
// ---------------------------------------------------------------------------

export interface KpiCardProps {
  label: string;
  value: number | string;
  sublabel?: string;
  onClick?: () => void;
  isLoading?: boolean;
}

// ---------------------------------------------------------------------------
// RegistrationAnalytics date range
// ---------------------------------------------------------------------------

export interface DateRange {
  /** ISO date string in YYYY-MM-DD format */
  startDate: string;
  /** ISO date string in YYYY-MM-DD format */
  endDate: string;
}

// ---------------------------------------------------------------------------
// NeedsAttentionPanel item
// ---------------------------------------------------------------------------

export interface AttentionItem {
  id: string;
  label: string;
  count: number;
  /** Accordion item ID for scroll/navigation */
  targetSectionId: string;
}

// ---------------------------------------------------------------------------
// DangerZone action
// ---------------------------------------------------------------------------

export interface DangerAction {
  id: string;
  name: string;
  description: string;
  confirmPhrase: string;
  onExecute: () => Promise<void>;
}
