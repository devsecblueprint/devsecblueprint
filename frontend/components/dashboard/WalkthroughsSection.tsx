'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { getWalkthroughsWithProgress } from '@/lib/walkthrough-client';
import { WalkthroughPreviewModal } from './WalkthroughPreviewModal';
import type { WalkthroughWithProgress } from '@/lib/types';

export function WalkthroughsSection() {
  const [walkthroughs, setWalkthroughs] = useState<WalkthroughWithProgress[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);
  const [previewWalkthrough, setPreviewWalkthrough] = useState<WalkthroughWithProgress | null>(null);

  const fetchWalkthroughs = useCallback(async () => {
    try {
      const data = await getWalkthroughsWithProgress();
      setWalkthroughs(data);
    } catch {
      setError(true);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWalkthroughs();
  }, [fetchWalkthroughs]);

  const inProgress = walkthroughs.filter(w => w.progress.status === 'in_progress');
  const allCompleted = walkthroughs.length > 0 && walkthroughs.every(w => w.progress.status === 'completed');
  const displayedWalkthroughs = inProgress.slice(0, 3);
  const hasMore = inProgress.length > 3;

  if (isLoading) {
    return (
      <section>
        <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6">
          Hands-On Walkthroughs
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-3" />
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-3" />
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4" />
              <div className="h-9 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mt-auto" />
            </Card>
          ))}
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section>
        <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6">
          Hands-On Walkthroughs
        </h2>
        <Card>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Start a hands-on walkthrough to practice real-world skills
          </p>
          <div className="mt-4">
            <Link
              href="/walkthroughs"
              className="inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-900 bg-amber-500 dark:bg-amber-400 rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
            >
              Browse Walkthroughs
            </Link>
          </div>
        </Card>
      </section>
    );
  }

  if (allCompleted) {
    return (
      <section>
        <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6">
          Hands-On Walkthroughs
        </h2>
        <Card className="text-center py-8">
          <div className="text-4xl mb-3" aria-hidden="true">🏆</div>
          <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            All walkthroughs completed! 🎉
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Great work! You can revisit any walkthrough anytime.
          </p>
          <div className="mt-4">
            <Link
              href="/walkthroughs"
              className="inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-900 bg-amber-500 dark:bg-amber-400 rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
            >
              Browse Walkthroughs
            </Link>
          </div>
        </Card>
      </section>
    );
  }

  if (inProgress.length === 0) {
    return (
      <section>
        <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6">
          Hands-On Walkthroughs
        </h2>
        <Card>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Start a hands-on walkthrough to practice real-world skills
          </p>
          <div className="mt-4">
            <Link
              href="/walkthroughs"
              className="inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-900 bg-amber-500 dark:bg-amber-400 rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
            >
              Browse Walkthroughs
            </Link>
          </div>
        </Card>
      </section>
    );
  }

  return (
    <section>
      <div className="flex items-center justify-between mb-4 sm:mb-6">
        <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
          Hands-On Walkthroughs
        </h2>
        {hasMore && (
          <Link
            href="/walkthroughs"
            className="text-sm font-medium text-amber-600 dark:text-amber-400 hover:text-amber-700 dark:hover:text-amber-300 transition-colors"
          >
            View All →
          </Link>
        )}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
        {displayedWalkthroughs.map((walkthrough) => (
          <Card key={walkthrough.id} className="flex flex-col gap-3">
            <div className="flex items-start justify-between gap-2">
              <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100 line-clamp-2">
                {walkthrough.title}
              </h3>
              <Badge
                variant={
                  walkthrough.difficulty === 'Beginner'
                    ? 'success'
                    : walkthrough.difficulty === 'Advanced'
                      ? 'warning'
                      : 'default'
                }
                size="sm"
              >
                {walkthrough.difficulty}
              </Badge>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              ~{walkthrough.estimatedTime} min
            </p>
            <div className="mt-auto pt-2">
              <button
                onClick={() => setPreviewWalkthrough(walkthrough)}
                className="inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-900 bg-amber-500 dark:bg-amber-400 rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
              >
                Preview
                <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </button>
            </div>
          </Card>
        ))}
      </div>
      {previewWalkthrough && (
        <WalkthroughPreviewModal
          walkthrough={previewWalkthrough}
          isOpen={true}
          onClose={() => setPreviewWalkthrough(null)}
          onProgressReset={() => {
            fetchWalkthroughs();
          }}
        />
      )}
    </section>
  );
}
