'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { format } from 'date-fns';
import { apiClient } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { KpiCard } from '@/app/admin/components/KpiCard';
import type {
  VideoAnalyticsItem,
  VideoAnalyticsResponse,
  VideoAnalyticsTier,
} from '@/lib/types';

type TierFilter = 'ALL' | VideoAnalyticsTier;
type SortKey =
  | 'title'
  | 'tier'
  | 'viewers'
  | 'completed'
  | 'completion'
  | 'avg'
  | 'last';
type SortDir = 'asc' | 'desc';

const FILTERS: { label: string; value: TierFilter }[] = [
  { label: 'All', value: 'ALL' },
  { label: 'Free', value: 'FREE' },
  { label: 'Builder', value: 'BUILDER' },
];

const COLUMNS: { key: SortKey; label: string; align: 'left' | 'right' }[] = [
  { key: 'title', label: 'Video', align: 'left' },
  { key: 'tier', label: 'Tier', align: 'left' },
  { key: 'viewers', label: 'Viewers', align: 'right' },
  { key: 'completed', label: 'Completed', align: 'right' },
  { key: 'completion', label: 'Completion', align: 'left' },
  { key: 'avg', label: 'Avg. progress', align: 'right' },
  { key: 'last', label: 'Last watched', align: 'left' },
];

const TIER_LABEL: Record<VideoAnalyticsTier, string> = {
  FREE: 'Free',
  BUILDER: 'Builder',
};

const TIER_BADGE: Record<VideoAnalyticsTier, string> = {
  FREE: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
  BUILDER: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
};

const NOT_READY_MESSAGE =
  'Analytics are still being prepared, try again in a moment.';

function formatDate(value?: string | null): string {
  if (!value) return '—';
  try {
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return value;
    return format(d, 'MMM d, yyyy h:mm a');
  } catch {
    return value;
  }
}

function clampPercent(n: number): number {
  return Math.max(0, Math.min(100, n));
}

function Bar({ percent }: { percent: number }) {
  return (
    <div
      className="h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden"
      aria-hidden="true"
    >
      <div
        className="h-full rounded-full bg-amber-500 dark:bg-amber-400"
        style={{ width: `${clampPercent(percent)}%` }}
      />
    </div>
  );
}

function compare(a: VideoAnalyticsItem, b: VideoAnalyticsItem, key: SortKey): number {
  switch (key) {
    case 'title':
      return a.title.localeCompare(b.title);
    case 'tier':
      return a.access_tier.localeCompare(b.access_tier);
    case 'viewers':
      return a.unique_viewers - b.unique_viewers;
    case 'completed':
      return a.completed - b.completed;
    case 'completion':
      return a.completion_rate - b.completion_rate;
    case 'avg':
      return a.avg_best_progress - b.avg_best_progress;
    case 'last':
      return (
        new Date(a.last_watched_at as string).getTime() -
        new Date(b.last_watched_at as string).getTime()
      );
  }
}

function LoadingSkeleton() {
  return (
    <div aria-busy="true" aria-label="Loading video analytics" className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="rounded-lg bg-gray-50 dark:bg-gray-800 p-4">
            <Skeleton className="h-8 w-20 mb-2" />
            <Skeleton className="h-4 w-28" />
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
      <div className="space-y-2">
        {[0, 1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    </div>
  );
}

function TierBlock({
  label,
  stats,
}: {
  label: string;
  stats: { viewers: number; completions: number; completion_rate: number };
}) {
  return (
    <div className="rounded-lg bg-gray-50 dark:bg-gray-800 p-4">
      <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2">
        {label}
      </h4>
      <dl className="flex gap-6 text-sm mb-3">
        <div>
          <dt className="text-xs text-gray-500 dark:text-gray-400">Viewers</dt>
          <dd className="font-semibold text-gray-900 dark:text-gray-100">
            {stats.viewers}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-gray-500 dark:text-gray-400">Completions</dt>
          <dd className="font-semibold text-gray-900 dark:text-gray-100">
            {stats.completions}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-gray-500 dark:text-gray-400">Completion rate</dt>
          <dd className="font-semibold text-amber-600 dark:text-amber-400">
            {stats.completion_rate}%
          </dd>
        </div>
      </dl>
      <Bar percent={stats.completion_rate} />
    </div>
  );
}

export function VideoAnalytics() {
  const [data, setData] = useState<VideoAnalyticsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<TierFilter>('ALL');
  const [sort, setSort] = useState<{ key: SortKey; dir: SortDir }>({
    key: 'viewers',
    dir: 'desc',
  });

  // Single request per call. Called once on mount and again only when the
  // admin presses "Try again". There is no polling.
  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { data: result, error: apiError, statusCode } =
        await apiClient.getVideoAnalytics();
      if (statusCode === 503) {
        setError(NOT_READY_MESSAGE);
      } else if (apiError || !result) {
        setError(apiError || 'Failed to load video analytics');
      } else {
        setData(result);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load video analytics');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const rows = useMemo(() => {
    if (!data) return [];
    const filtered =
      filter === 'ALL'
        ? data.videos
        : data.videos.filter((v) => v.access_tier === filter);
    const factor = sort.dir === 'asc' ? 1 : -1;
    return [...filtered].sort((a, b) => {
      if (sort.key === 'last') {
        // Videos never watched always sort last, whatever the direction
        if (!a.last_watched_at && !b.last_watched_at) return a.title.localeCompare(b.title);
        if (!a.last_watched_at) return 1;
        if (!b.last_watched_at) return -1;
      }
      const result = compare(a, b, sort.key) * factor;
      return result !== 0 ? result : a.title.localeCompare(b.title);
    });
  }, [data, filter, sort]);

  const handleSort = (key: SortKey) => {
    setSort((prev) =>
      prev.key === key
        ? { key, dir: prev.dir === 'asc' ? 'desc' : 'asc' }
        : { key, dir: key === 'title' || key === 'tier' ? 'asc' : 'desc' }
    );
  };

  if (isLoading && !data) {
    return <LoadingSkeleton />;
  }

  if (error) {
    return (
      <div
        role="alert"
        className="rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 p-4"
      >
        <p className="text-sm text-red-700 dark:text-red-300 mb-3">{error}</p>
        <button
          type="button"
          onClick={load}
          className="min-h-[44px] px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-gray-900 font-semibold rounded-lg transition-colors"
        >
          Try again
        </button>
      </div>
    );
  }

  if (!data) return null;

  if (data.videos.length === 0) {
    return (
      <Card>
        <p className="text-center text-gray-500 dark:text-gray-400 py-8">
          No videos yet
        </p>
      </Card>
    );
  }

  const staleMinutes = Math.max(
    0,
    Math.round((Date.now() - new Date(data.generated_at).getTime()) / 60000)
  );
  const topMax = Math.max(1, ...data.top_videos.map((v) => v.unique_viewers));

  return (
    <div className="space-y-6">
      {/* As-of line */}
      <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-gray-500 dark:text-gray-400">
        <p>As of {formatDate(data.generated_at)}</p>
        <p>Signed-in members only</p>
      </div>

      {data.stale && (
        <div
          role="status"
          className="rounded-lg border border-yellow-300 dark:border-yellow-700 bg-yellow-50 dark:bg-yellow-900/20 px-4 py-3 text-sm text-yellow-800 dark:text-yellow-200"
        >
          Showing cached data from {staleMinutes} {staleMinutes === 1 ? 'minute' : 'minutes'} ago. A refresh is running.
        </div>
      )}

      {/* Summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard label="Distinct viewers" value={data.totals.distinct_viewers} />
        <KpiCard label="Active last 7 days" value={data.totals.active_7d} />
        <KpiCard label="Active last 30 days" value={data.totals.active_30d} />
        <KpiCard label="Completion rate" value={`${data.totals.completion_rate}%`} />
      </div>

      {/* Most watched + tier panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card padding="sm">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Most watched
          </h3>
          {data.top_videos.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400">No views yet</p>
          ) : (
            <ol className="space-y-3" aria-label="Most watched videos">
              {data.top_videos.map((video, index) => (
                <li key={video.id} className="flex items-center gap-3">
                  <span className="w-5 text-sm font-semibold text-gray-500 dark:text-gray-400">
                    {index + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                      {video.title}
                    </p>
                    <Bar percent={(video.unique_viewers / topMax) * 100} />
                  </div>
                  <span className="text-sm font-semibold text-gray-900 dark:text-gray-100 whitespace-nowrap">
                    {video.unique_viewers} {video.unique_viewers === 1 ? 'viewer' : 'viewers'}
                  </span>
                </li>
              ))}
            </ol>
          )}
        </Card>

        <Card padding="sm">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            By access tier
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <TierBlock label="Free" stats={data.by_tier.FREE} />
            <TierBlock label="Builder" stats={data.by_tier.BUILDER} />
          </div>
        </Card>
      </div>

      {/* All videos */}
      <Card padding="sm">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            All videos
          </h3>
          <div className="flex gap-2" role="group" aria-label="Filter by access tier">
            {FILTERS.map((f) => (
              <button
                key={f.value}
                type="button"
                aria-pressed={filter === f.value}
                onClick={() => setFilter(f.value)}
                className={`min-h-[44px] min-w-[44px] px-4 py-2 text-sm font-medium rounded-lg transition-colors whitespace-nowrap ${
                  filter === f.value
                    ? 'bg-yellow-500 text-gray-900'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                {COLUMNS.map((col) => {
                  const active = sort.key === col.key;
                  return (
                    <th
                      key={col.key}
                      scope="col"
                      aria-sort={
                        active
                          ? sort.dir === 'asc'
                            ? 'ascending'
                            : 'descending'
                          : undefined
                      }
                      className={`py-1 px-2 font-medium text-gray-500 dark:text-gray-400 ${
                        col.align === 'right' ? 'text-right' : 'text-left'
                      }`}
                    >
                      <button
                        type="button"
                        onClick={() => handleSort(col.key)}
                        className="inline-flex items-center gap-1 min-h-[44px] px-2 whitespace-nowrap rounded-sm hover:text-gray-900 dark:hover:text-gray-100 focus:outline-hidden focus:ring-2 focus:ring-yellow-500"
                      >
                        {col.label}
                        <span aria-hidden="true">
                          {active ? (sort.dir === 'asc' ? '▲' : '▼') : ''}
                        </span>
                      </button>
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 ? (
                <tr>
                  <td
                    colSpan={COLUMNS.length}
                    className="py-8 text-center text-gray-500 dark:text-gray-400"
                  >
                    No videos in this tier
                  </td>
                </tr>
              ) : (
                rows.map((video) => {
                  const hasViewers = video.unique_viewers > 0;
                  return (
                    <tr
                      key={video.id}
                      className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-900/50"
                    >
                      <th
                        scope="row"
                        className="py-3 px-4 text-left font-medium text-gray-900 dark:text-gray-100"
                      >
                        {video.title}
                      </th>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${TIER_BADGE[video.access_tier]}`}
                        >
                          {TIER_LABEL[video.access_tier]}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right text-gray-700 dark:text-gray-300">
                        {video.unique_viewers}
                      </td>
                      <td className="py-3 px-4 text-right text-gray-700 dark:text-gray-300">
                        {video.completed}
                      </td>
                      <td className="py-3 px-4">
                        {hasViewers ? (
                          <div className="flex items-center gap-2 min-w-[7rem]">
                            <span className="w-10 text-gray-700 dark:text-gray-300">
                              {video.completion_rate}%
                            </span>
                            <Bar percent={video.completion_rate} />
                          </div>
                        ) : (
                          <span className="text-gray-400 dark:text-gray-500">—</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right text-gray-700 dark:text-gray-300">
                        {hasViewers ? `${video.avg_best_progress}%` : '—'}
                      </td>
                      <td className="py-3 px-4 text-gray-600 dark:text-gray-400 whitespace-nowrap">
                        {formatDate(video.last_watched_at)}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </Card>

      <p className="text-xs text-gray-500 dark:text-gray-400">
        Only aggregate numbers are shown. Individual viewers are never listed.
      </p>
    </div>
  );
}
