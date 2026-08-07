'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { KpiCard } from './KpiCard';

// ---------------------------------------------------------------------------
// Types matching the GET /admin/journey-analytics API response
// ---------------------------------------------------------------------------

interface PhaseCompletionFunnelItem {
  phase: number;
  completed_count: number;
  avg_days: number;
}

interface TaskCompletionRateItem {
  task_id: string;
  phase: number;
  completion_rate: number;
}

interface TimelineEntry {
  date: string;
  count: number;
}

interface JourneyAnalyticsData {
  totals: {
    journeys_started: number;
    journeys_completed: number;
    completion_rate: number;
    average_duration_days: number;
  };
  phase_distribution: Record<string, number>;
  phase_completion_funnel: PhaseCompletionFunnelItem[];
  task_completion_rates: TaskCompletionRateItem[];
  key_rates: {
    discord_connection_rate: number;
    prerequisites_completion_rate: number;
  };
  timeline_30d: {
    starts: TimelineEntry[];
    completions: TimelineEntry[];
  };
}

// ---------------------------------------------------------------------------
// Sorting helpers
// ---------------------------------------------------------------------------

type SortKey = 'task_id' | 'phase' | 'completion_rate';
type SortDir = 'asc' | 'desc';

function sortTasks(
  tasks: TaskCompletionRateItem[],
  key: SortKey,
  dir: SortDir
): TaskCompletionRateItem[] {
  return [...tasks].sort((a, b) => {
    const aVal = a[key];
    const bVal = b[key];
    if (aVal < bVal) return dir === 'asc' ? -1 : 1;
    if (aVal > bVal) return dir === 'asc' ? 1 : -1;
    return 0;
  });
}

// ---------------------------------------------------------------------------
// Loading skeleton
// ---------------------------------------------------------------------------

function LoadingSkeleton() {
  return (
    <section aria-label="Builder Journey Analytics" aria-busy="true">
      <Card>
        <div className="animate-pulse space-y-6">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-48" />
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-20 bg-gray-100 dark:bg-gray-800 rounded-lg" />
            ))}
          </div>
          <div className="h-40 bg-gray-100 dark:bg-gray-800 rounded-lg" />
          <div className="h-32 bg-gray-100 dark:bg-gray-800 rounded-lg" />
        </div>
      </Card>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Error state
// ---------------------------------------------------------------------------

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <section aria-label="Builder Journey Analytics">
      <Card>
        <div className="text-center py-8">
          <p className="text-red-500 dark:text-red-400 mb-4">{message}</p>
          <button
            onClick={onRetry}
            className="px-5 py-3 bg-amber-500 dark:bg-amber-400 text-gray-900 font-semibold rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 min-h-[44px]"
          >
            Retry
          </button>
        </div>
      </Card>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Phase Funnel Visualization
// ---------------------------------------------------------------------------

function PhaseFunnel({ funnel }: { funnel: PhaseCompletionFunnelItem[] }) {
  const maxCount = Math.max(...funnel.map((p) => p.completed_count), 1);

  return (
    <div className="space-y-3">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
        Phase Completion Funnel
      </h3>
      <div className="space-y-2">
        {funnel.map((item) => {
          const widthPct = (item.completed_count / maxCount) * 100;
          return (
            <div key={item.phase} className="space-y-1">
              <p className="text-sm text-gray-700 dark:text-gray-300">
                Phase {item.phase}: {item.completed_count} ({item.avg_days} days avg)
              </p>
              <div className="w-full bg-gray-100 dark:bg-gray-800 rounded-full h-4">
                <div
                  className="bg-amber-500 h-4 rounded-full transition-all"
                  style={{ width: `${widthPct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Task Completion Rates Table
// ---------------------------------------------------------------------------

function TaskCompletionTable({ tasks }: { tasks: TaskCompletionRateItem[] }) {
  const [sortKey, setSortKey] = useState<SortKey>('task_id');
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const sorted = sortTasks(tasks, sortKey, sortDir);

  const headerClass =
    'pb-2 font-medium cursor-pointer select-none hover:text-amber-500 dark:hover:text-amber-400 transition-colors';

  function renderArrow(key: SortKey) {
    if (sortKey !== key) return null;
    return <span className="ml-1">{sortDir === 'asc' ? '↑' : '↓'}</span>;
  }

  return (
    <div className="space-y-3">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
        Task Completion Rates
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
              <th className={headerClass} onClick={() => handleSort('task_id')}>
                Task ID{renderArrow('task_id')}
              </th>
              <th className={headerClass} onClick={() => handleSort('phase')}>
                Phase{renderArrow('phase')}
              </th>
              <th className={headerClass} onClick={() => handleSort('completion_rate')}>
                Completion Rate{renderArrow('completion_rate')}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {sorted.map((task) => (
              <tr key={task.task_id}>
                <td className="py-2 text-gray-900 dark:text-gray-100">
                  {task.task_id}
                </td>
                <td className="py-2 text-gray-600 dark:text-gray-300">
                  {task.phase}
                </td>
                <td className="py-2 text-gray-600 dark:text-gray-300">
                  {task.completion_rate}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 30-Day Timeline
// ---------------------------------------------------------------------------

function Timeline30d({ timeline }: { timeline: JourneyAnalyticsData['timeline_30d'] }) {
  const maxCount = Math.max(
    ...timeline.starts.map((s) => s.count),
    ...timeline.completions.map((c) => c.count),
    1
  );

  return (
    <div className="space-y-3">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
        Last 30 Days
      </h3>
      <div className="space-y-4">
        {/* Starts row */}
        <div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Starts</p>
          <div className="flex items-end gap-[2px] h-8">
            {timeline.starts.map((entry) => {
              const heightPct = (entry.count / maxCount) * 100;
              return (
                <div
                  key={entry.date}
                  className="flex-1 bg-amber-500 rounded-t-sm min-w-[3px]"
                  style={{ height: `${Math.max(heightPct, 4)}%` }}
                  title={`${entry.date}: ${entry.count} starts`}
                />
              );
            })}
          </div>
        </div>

        {/* Completions row */}
        <div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Completions</p>
          <div className="flex items-end gap-[2px] h-8">
            {timeline.completions.map((entry) => {
              const heightPct = (entry.count / maxCount) * 100;
              return (
                <div
                  key={entry.date}
                  className="flex-1 bg-green-500 rounded-t-sm min-w-[3px]"
                  style={{ height: `${Math.max(heightPct, 4)}%` }}
                  title={`${entry.date}: ${entry.count} completions`}
                />
              );
            })}
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
          <span className="flex items-center gap-1">
            <span className="inline-block w-3 h-3 bg-amber-500 rounded-sm" />
            Starts
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block w-3 h-3 bg-green-500 rounded-sm" />
            Completions
          </span>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function JourneyAnalyticsSection() {
  const [data, setData] = useState<JourneyAnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    const response = await apiClient.get<JourneyAnalyticsData>('/admin/journey-analytics');
    if (response.error) {
      setError(response.error);
    } else if (response.data) {
      setData(response.data);
    }
    setIsLoading(false);
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (error || !data) {
    return (
      <ErrorState
        message={error || 'Failed to load journey analytics'}
        onRetry={fetchData}
      />
    );
  }

  return (
    <section aria-label="Builder Journey Analytics">
      <Card>
        <div className="space-y-8">
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
            Builder Journey Analytics
          </h2>

          {/* KPI Cards Row */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard
              label="Journeys Started"
              value={data.totals.journeys_started}
            />
            <KpiCard
              label="Journeys Completed"
              value={data.totals.journeys_completed}
            />
            <KpiCard
              label="Completion Rate"
              value={`${data.totals.completion_rate}%`}
            />
            <KpiCard
              label="Avg Duration"
              value={`${data.totals.average_duration_days} days`}
            />
          </div>

          {/* Phase Funnel */}
          <PhaseFunnel funnel={data.phase_completion_funnel} />

          {/* Task Completion Rates Table */}
          <TaskCompletionTable tasks={data.task_completion_rates} />

          {/* 30-Day Timeline */}
          <Timeline30d timeline={data.timeline_30d} />
        </div>
      </Card>
    </section>
  );
}
