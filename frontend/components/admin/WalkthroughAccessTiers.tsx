'use client';

import { useEffect, useState, useCallback } from 'react';
import { apiClient } from '@/lib/api';
import { WALKTHROUGHS_DATA } from '@/lib/walkthroughs-data';
import { Spinner } from '@/components/ui/Spinner';

interface WalkthroughTierItem {
  id: string;
  title: string;
  difficulty: string;
  accessTier: 'FREE' | 'BUILDER';
}

export function WalkthroughAccessTiers() {
  const [walkthroughs, setWalkthroughs] = useState<WalkthroughTierItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pendingIds, setPendingIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchAccessTiers();
  }, []);

  const fetchAccessTiers = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { data, error: apiError } = await apiClient.getAdminWalkthroughAccessTiers();
      if (apiError) {
        setError(apiError);
        return;
      }

      const tiers = data?.access_tiers || {};

      const items: WalkthroughTierItem[] = WALKTHROUGHS_DATA.map((wt) => ({
        id: wt.id,
        title: wt.title,
        difficulty: wt.difficulty,
        accessTier: (tiers[wt.id] as 'FREE' | 'BUILDER') || 'FREE',
      }));

      setWalkthroughs(items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch access tiers');
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleTier = useCallback(async (walkthroughId: string, currentTier: 'FREE' | 'BUILDER') => {
    const newTier = currentTier === 'FREE' ? 'BUILDER' : 'FREE';

    // Optimistic update — toggle immediately for smooth UX
    setWalkthroughs((prev) =>
      prev.map((wt) =>
        wt.id === walkthroughId ? { ...wt, accessTier: newTier } : wt
      )
    );
    setPendingIds((prev) => new Set(prev).add(walkthroughId));

    try {
      const { error: apiError } = await apiClient.setWalkthroughAccessTier(walkthroughId, newTier);
      if (apiError) {
        // Revert on error
        setWalkthroughs((prev) =>
          prev.map((wt) =>
            wt.id === walkthroughId ? { ...wt, accessTier: currentTier } : wt
          )
        );
      }
    } catch {
      // Revert on error
      setWalkthroughs((prev) =>
        prev.map((wt) =>
          wt.id === walkthroughId ? { ...wt, accessTier: currentTier } : wt
        )
      );
    } finally {
      setPendingIds((prev) => {
        const next = new Set(prev);
        next.delete(walkthroughId);
        return next;
      });
    }
  }, []);

  if (isLoading) {
    return (
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Walkthrough Access Tiers
        </h2>
        <div className="flex items-center justify-center py-12">
          <Spinner size="lg" />
        </div>
      </div>
    );
  }

  if (error && walkthroughs.length === 0) {
    return (
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Walkthrough Access Tiers
        </h2>
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
          <button
            onClick={fetchAccessTiers}
            className="mt-2 text-sm font-medium text-red-600 dark:text-red-400 hover:text-red-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  const lockedCount = walkthroughs.filter((w) => w.accessTier === 'BUILDER').length;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            Walkthrough Access Tiers
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {lockedCount} of {walkthroughs.length} walkthroughs locked to Builder
          </p>
        </div>
      </div>

      <div className="space-y-2">
        {walkthroughs.map((wt) => {
          const isBuilder = wt.accessTier === 'BUILDER';
          const isPending = pendingIds.has(wt.id);

          return (
            <div
              key={wt.id}
              className={`flex items-center justify-between rounded-lg border px-4 py-3 transition-colors duration-200 ${
                isBuilder
                  ? 'border-amber-200 dark:border-amber-800/50 bg-amber-50/50 dark:bg-amber-900/10'
                  : 'border-gray-200 dark:border-gray-700'
              }`}
            >
              <div className="flex-1 min-w-0 mr-4">
                <div className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                  {wt.title}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {wt.difficulty}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => handleToggleTier(wt.id, wt.accessTier)}
                  disabled={isPending}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-500 dark:focus:ring-offset-gray-900 disabled:cursor-wait ${
                    isBuilder
                      ? 'bg-amber-500'
                      : 'bg-gray-300 dark:bg-gray-600'
                  }`}
                  role="switch"
                  aria-checked={isBuilder}
                  aria-label={`${wt.title}: ${isBuilder ? 'Builder (click to set Free)' : 'Free (click to set Builder)'}`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition-transform duration-200 ease-in-out ${
                      isBuilder ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
                <span
                  className={`text-xs font-semibold w-14 transition-colors duration-200 ${
                    isBuilder
                      ? 'text-amber-700 dark:text-amber-400'
                      : 'text-gray-400 dark:text-gray-500'
                  }`}
                >
                  {isBuilder ? 'Builder' : 'Free'}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
