'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { apiClient } from '@/lib/api';
import type {
  ActiveSessionsResponse,
  CapstoneSubmissionsResponse,
  ModuleHealthResponse,
  RegistryStatusResponse,
} from '@/lib/api';
import type {
  AdminDashboardContextValue,
  AnalyticsData,
  AttentionCounts,
  KpiMetric,
} from './types';
import { buildKpiMetrics, deriveAttentionCounts } from './utils';

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

const AdminDashboardContext = createContext<AdminDashboardContextValue | null>(
  null
);

// ---------------------------------------------------------------------------
// Provider component
// ---------------------------------------------------------------------------

export function AdminDashboardProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  // Raw API data state
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [activeSessions, setActiveSessions] =
    useState<ActiveSessionsResponse | null>(null);
  const [submissions, setSubmissions] =
    useState<CapstoneSubmissionsResponse | null>(null);
  const [moduleHealth, setModuleHealth] =
    useState<ModuleHealthResponse | null>(null);
  const [registryStatus, setRegistryStatus] =
    useState<RegistryStatusResponse | null>(null);

  // Loading and error states
  const [isLoading, setIsLoading] = useState(true);
  const [errors, setErrors] = useState<Record<string, string | null>>({
    analytics: null,
    activeSessions: null,
    submissions: null,
    moduleHealth: null,
    registryStatus: null,
  });

  // Sessions modal toggle
  const [sessionsModalOpen, setSessionsModalOpen] = useState(false);

  // ---------------------------------------------------------------------------
  // Data fetching
  // ---------------------------------------------------------------------------

  const fetchAll = useCallback(async () => {
    setIsLoading(true);

    const [
      analyticsResult,
      sessionsResult,
      submissionsResult,
      moduleHealthResult,
      registryResult,
    ] = await Promise.allSettled([
      apiClient.getAnalytics(),
      apiClient.getActiveSessions(),
      apiClient.getCapstoneSubmissions(),
      apiClient.getModuleHealth(),
      apiClient.getRegistryStatus(),
    ]);

    const newErrors: Record<string, string | null> = {
      analytics: null,
      activeSessions: null,
      submissions: null,
      moduleHealth: null,
      registryStatus: null,
    };

    // Process analytics
    if (analyticsResult.status === 'fulfilled') {
      const { data, error } = analyticsResult.value;
      if (data) {
        setAnalytics(data as unknown as AnalyticsData);
      } else {
        newErrors.analytics = error ?? 'Failed to fetch analytics';
      }
    } else {
      newErrors.analytics = analyticsResult.reason?.message ?? 'Request failed';
    }

    // Process active sessions
    if (sessionsResult.status === 'fulfilled') {
      const { data, error } = sessionsResult.value;
      if (data) {
        setActiveSessions(data);
      } else {
        newErrors.activeSessions = error ?? 'Failed to fetch sessions';
      }
    } else {
      newErrors.activeSessions =
        sessionsResult.reason?.message ?? 'Request failed';
    }

    // Process submissions
    if (submissionsResult.status === 'fulfilled') {
      const { data, error } = submissionsResult.value;
      if (data) {
        setSubmissions(data);
      } else {
        newErrors.submissions = error ?? 'Failed to fetch submissions';
      }
    } else {
      newErrors.submissions =
        submissionsResult.reason?.message ?? 'Request failed';
    }

    // Process module health
    if (moduleHealthResult.status === 'fulfilled') {
      const { data, error } = moduleHealthResult.value;
      if (data) {
        setModuleHealth(data);
      } else {
        newErrors.moduleHealth = error ?? 'Failed to fetch module health';
      }
    } else {
      newErrors.moduleHealth =
        moduleHealthResult.reason?.message ?? 'Request failed';
    }

    // Process registry status
    if (registryResult.status === 'fulfilled') {
      const { data, error } = registryResult.value;
      if (data) {
        setRegistryStatus(data);
      } else {
        newErrors.registryStatus = error ?? 'Failed to fetch registry status';
      }
    } else {
      newErrors.registryStatus =
        registryResult.reason?.message ?? 'Request failed';
    }

    setErrors(newErrors);
    setIsLoading(false);
  }, []);

  const refetchAnalytics = useCallback(async () => {
    try {
      const { data, error } = await apiClient.getAnalytics();
      if (data) {
        setAnalytics(data as unknown as AnalyticsData);
        setErrors((prev) => ({ ...prev, analytics: null }));
      } else {
        setErrors((prev) => ({
          ...prev,
          analytics: error ?? 'Failed to fetch analytics',
        }));
      }
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Failed to fetch analytics';
      setErrors((prev) => ({ ...prev, analytics: message }));
    }
  }, []);

  // Fetch on mount
  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  // ---------------------------------------------------------------------------
  // Derived data
  // ---------------------------------------------------------------------------

  const openSessionsModal = useCallback(() => {
    setSessionsModalOpen(true);
  }, []);

  const closeSessionsModal = useCallback(() => {
    setSessionsModalOpen(false);
  }, []);

  const attentionCounts: AttentionCounts = useMemo(
    () => deriveAttentionCounts(submissions, moduleHealth, registryStatus, 0),
    [submissions, moduleHealth, registryStatus]
  );

  const kpiMetrics: KpiMetric[] = useMemo(
    () =>
      buildKpiMetrics(
        analytics,
        activeSessions?.total_active ?? null,
        openSessionsModal
      ),
    [analytics, activeSessions, openSessionsModal]
  );

  // ---------------------------------------------------------------------------
  // Context value (stable reference via useMemo)
  // ---------------------------------------------------------------------------

  const contextValue: AdminDashboardContextValue = useMemo(
    () => ({
      analytics,
      activeSessions,
      submissions,
      moduleHealth,
      registryStatus,
      attentionCounts,
      kpiMetrics,
      isLoading,
      errors,
      sessionsModalOpen,
      refetchAll: fetchAll,
      refetchAnalytics,
      openSessionsModal,
      closeSessionsModal,
    }),
    [
      analytics,
      activeSessions,
      submissions,
      moduleHealth,
      registryStatus,
      attentionCounts,
      kpiMetrics,
      isLoading,
      errors,
      sessionsModalOpen,
      fetchAll,
      refetchAnalytics,
      openSessionsModal,
      closeSessionsModal,
    ]
  );

  return (
    <AdminDashboardContext.Provider value={contextValue}>
      {children}
    </AdminDashboardContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Consumer hook
// ---------------------------------------------------------------------------

/**
 * Hook to consume AdminDashboardContext.
 * Throws if used outside of AdminDashboardProvider.
 */
export function useAdminContext(): AdminDashboardContextValue {
  const context = useContext(AdminDashboardContext);
  if (!context) {
    throw new Error(
      'useAdminContext must be used within an AdminDashboardProvider'
    );
  }
  return context;
}
