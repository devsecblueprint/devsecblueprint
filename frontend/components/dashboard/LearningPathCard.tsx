'use client';

import Link from 'next/link';
import { Card } from '@/components/ui/Card';
import { ProgressBar } from '@/components/ui/ProgressBar';

export interface LearningPathCardProps {
  title: string;
  percentComplete: number;
  completedPages: number;
  totalPages: number;
  nextLessonTitle?: string;
  actionHref: string;
  actionLabel: string;
}

export function LearningPathCard({
  title,
  percentComplete,
  completedPages,
  totalPages,
  nextLessonTitle,
  actionHref,
  actionLabel,
}: LearningPathCardProps) {
  return (
    <Card className="flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100 leading-tight">
          {title}
        </h3>
        <span className="text-sm font-medium text-gray-600 dark:text-gray-400 whitespace-nowrap">
          {percentComplete}%
        </span>
      </div>

      <ProgressBar percentage={percentComplete} height="sm" />

      <p className="text-sm text-gray-600 dark:text-gray-400">
        {completedPages} of {totalPages} lessons completed
      </p>

      {nextLessonTitle && (
        <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
          Next:{' '}
          <span className="text-gray-900 dark:text-gray-100 font-medium">
            {nextLessonTitle}
          </span>
        </p>
      )}

      <div className="mt-auto pt-2">
        <Link
          href={actionHref}
          className="inline-flex items-center justify-center px-4 py-2 text-sm font-semibold text-gray-900 bg-amber-500 dark:bg-amber-400 rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
        >
          {actionLabel}
          <svg
            className="w-4 h-4 ml-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M14 5l7 7m0 0l-7 7m7-7H3"
            />
          </svg>
        </Link>
      </div>
    </Card>
  );
}
