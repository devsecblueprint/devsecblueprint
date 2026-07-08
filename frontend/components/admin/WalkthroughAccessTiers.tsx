'use client';

import { useEffect, useState } from 'react';
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
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

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

      // Merge with static walkthrough data
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

  const handleToggleTier = async (walkthroughId: string, currentTier: 'FREE' | 'BUILDER') => {
    const newTier = currentTier === 'FREE' ? 'BUILDER' : 'FREE';
    setUpdatingId(walkthroughId);
    setError(null);
    setSuccessMessage(null);

    try {
      const { error: apiError } = await apiClient.setWalkthroughAccessTier(walkthroughId, newTier);
      if (apiError) {
        setError(apiError);
        return;
      }

      // Update local state
      setWalkthroughs((prev) =>
        prev.map((wt) =>
          wt.id === walkthroughId ? { ...wt, accessTier: newTier } : wt
        )
      );

      const wtTitle = walkthroughs.find((w) => w.id === walkthroughId)?.title || walkthroughId;
      setSuccessMessage(`${wtTitle} set to ${newTier}`);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update access tier');
    } finally {
      setUpdatingId(null);
    }
  };

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

      {successMessage && (
        <div className="mb-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg px-4 py-2">
          <p className="text-sm text-green-800 dark:text-green-200">{successMessage}</p>
        </div>
      )}

      {error && walkthroughs.length > 0 && (
        <div className="mb-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-4 py-2">
          <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      <div className="space-y-2">
        {walkthroughs.map((wt) => (
          <div
            key={wt.id}
            className="flex items-center justify-between rounded-lg border border-gray-200 dark:border-gray-700 px-4 py-3"
          >
            <div className="flex-1 min-w-0 mr-4">
              <div className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                {wt.title}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                {wt.difficulty}
              </div>
            </div>
            <button
              onClick={() => handleToggleTier(wt.id, wt.accessTier)}
              disabled={updatingId === wt.id}
              className={`relative inline-flex h-7 w-14 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 ${
                wt.accessTier === 'BUILDER'
                  ? 'bg-amber-500 focus:ring-amber-500'
                  : 'bg-gray-300 dark:bg-gray-600 focus:ring-gray-400'
              }`}
              role="switch"
              aria-checked={wt.accessTier === 'BUILDER'}
              aria-label={`Set ${wt.title} to ${wt.accessTier === 'BUILDER' ? 'FREE' : 'BUILDER'}`}
            >
              <span
                className={`pointer-events-none inline-block h-6 w-6 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                  wt.accessTier === 'BUILDER' ? 'translate-x-7' : 'translate-x-0'
                }`}
              />
              <span className="absolute inset-0 flex items-center justify-center">
                {updatingId === wt.id ? (
                  <Spinner size="sm" />
                ) : (
                  <span
                    className={`text-[10px] font-bold ${
                      wt.accessTier === 'BUILDER'
                        ? 'text-white ml-[-8px]'
                        : 'text-gray-500 dark:text-gray-300 ml-[8px]'
                    }`}
                  >
                    {wt.accessTier === 'BUILDER' ? '' : ''}
                  </span>
                )}
              </span>
            </button>
            <span
              className={`ml-3 text-xs font-semibold w-16 text-center ${
                wt.accessTier === 'BUILDER'
                  ? 'text-amber-700 dark:text-amber-400'
                  : 'text-gray-500 dark:text-gray-400'
              }`}
            >
              {wt.accessTier === 'BUILDER' ? 'Builder' : 'Free'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
