'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Badge } from '@/components/ui/Badge';
import { apiClient } from '@/lib/api';
import type { WalkthroughWithProgress } from '@/lib/types';

interface WalkthroughPreviewModalProps {
  walkthrough: WalkthroughWithProgress;
  isOpen: boolean;
  onClose: () => void;
  onProgressReset?: () => void;
}

export function WalkthroughPreviewModal({
  walkthrough,
  isOpen,
  onClose,
  onProgressReset,
}: WalkthroughPreviewModalProps) {
  const [isResetting, setIsResetting] = useState(false);
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  if (!isOpen) return null;

  const isCompleted = walkthrough.progress.status === 'completed';
  const isInProgress = walkthrough.progress.status === 'in_progress';

  const handleReset = async () => {
    setIsResetting(true);
    try {
      await apiClient.resetWalkthroughProgress(walkthrough.id);
      onProgressReset?.();
      onClose();
    } catch (err) {
      console.error('Failed to reset walkthrough progress:', err);
    } finally {
      setIsResetting(false);
      setShowResetConfirm(false);
    }
  };

  const handleStartWalkthrough = async () => {
    // Mark as in_progress if not already started
    if (walkthrough.progress.status === 'not_started') {
      try {
        await apiClient.updateWalkthroughProgress(walkthrough.id, 'in_progress');
      } catch (err) {
        console.error('Failed to start walkthrough:', err);
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-800">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {walkthrough.title}
              </h2>
              <div className="flex items-center gap-2 mt-2">
                <Badge
                  variant={
                    walkthrough.difficulty === 'Beginner' ? 'success' :
                    walkthrough.difficulty === 'Advanced' ? 'warning' : 'default'
                  }
                  size="sm"
                >
                  {walkthrough.difficulty}
                </Badge>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  ~{walkthrough.estimatedTime} min
                </span>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              aria-label="Close preview"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {walkthrough.description}
          </p>

          {/* Topics */}
          {walkthrough.topics.length > 0 && (
            <div>
              <h3 className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
                Topics Covered
              </h3>
              <div className="flex flex-wrap gap-2">
                {walkthrough.topics.map((topic) => (
                  <span
                    key={topic}
                    className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300"
                  >
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Prerequisites */}
          {walkthrough.prerequisites.length > 0 && (
            <div>
              <h3 className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
                Prerequisites
              </h3>
              <ul className="list-disc list-inside text-sm text-gray-600 dark:text-gray-400 space-y-1">
                {walkthrough.prerequisites.map((prereq) => (
                  <li key={prereq}>{prereq}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Repository */}
          {walkthrough.repositoryUrl && (
            <div>
              <h3 className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
                Repository
              </h3>
              <a
                href={walkthrough.repositoryUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-sm text-amber-500 dark:text-amber-400 hover:underline"
              >
                {walkthrough.repository}
                <svg className="w-3.5 h-3.5 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
            </div>
          )}

          {/* Status */}
          {(isCompleted || isInProgress) && (
            <div className="flex items-center gap-2 pt-2 border-t border-gray-200 dark:border-gray-800">
              <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${
                isCompleted ? 'text-green-600 dark:text-green-400' : 'text-amber-600 dark:text-amber-400'
              }`}>
                <span className={`w-2 h-2 rounded-full ${isCompleted ? 'bg-green-500' : 'bg-amber-500'}`} aria-hidden="true" />
                {isCompleted ? 'Completed' : 'In Progress'}
              </span>
            </div>
          )}
        </div>

        {/* Footer actions */}
        <div className="p-6 border-t border-gray-200 dark:border-gray-800">
          {showResetConfirm ? (
            <div className="space-y-3">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Are you sure? This will reset your progress for this walkthrough.
              </p>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleReset}
                  disabled={isResetting}
                  className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-red-500 hover:bg-red-600 rounded-lg transition-colors disabled:opacity-50"
                >
                  {isResetting ? 'Resetting...' : 'Yes, Reset'}
                </button>
                <button
                  onClick={() => setShowResetConfirm(false)}
                  className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Link
                  href={`/walkthroughs/${walkthrough.id}`}
                  onClick={handleStartWalkthrough}
                  className="inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-900 bg-amber-500 dark:bg-amber-400 rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
                >
                  {isCompleted ? 'Revisit' : isInProgress ? 'Continue' : 'Start Walkthrough'}
                  <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </Link>
              </div>
              {(isCompleted || isInProgress) && (
                <button
                  onClick={() => setShowResetConfirm(true)}
                  className="inline-flex items-center px-3 py-2 text-xs font-medium text-red-500 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg transition-colors"
                >
                  ↺ Reset Progress
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
