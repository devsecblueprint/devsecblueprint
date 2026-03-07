'use client';

import { WalkthroughWithProgress } from '@/lib/types';
import { Badge } from '@/components/ui/Badge';

export interface WalkthroughCardProps {
  walkthrough: WalkthroughWithProgress;
}

export function WalkthroughCard({ walkthrough }: WalkthroughCardProps) {
  const difficultyVariant = {
    'Beginner': 'success' as const,
    'Intermediate': 'warning' as const,
    'Advanced': 'default' as const,
  }[walkthrough.difficulty];

  const progressLabel = {
    'not_started': 'Not Started',
    'in_progress': 'In Progress',
    'completed': 'Completed',
  }[walkthrough.progress.status];

  const progressColor = {
    'not_started': 'text-gray-500 dark:text-gray-400',
    'in_progress': 'text-primary-500 dark:text-primary-400',
    'completed': 'text-green-600 dark:text-green-400',
  }[walkthrough.progress.status];

  return (
    <a
      href={`/walkthroughs/${walkthrough.id}`}
      className="block group"
    >
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-6 hover:border-primary-400 dark:hover:border-primary-400 transition-all hover:shadow-lg h-full flex flex-col">
        {/* Header with Title and Difficulty */}
        <div className="flex items-start justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 group-hover:text-primary-500 dark:group-hover:text-primary-400 transition-colors flex-1 pr-3">
            {walkthrough.title}
          </h2>
          <Badge variant={difficultyVariant} size="sm">
            {walkthrough.difficulty}
          </Badge>
        </div>

        {/* Description */}
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 line-clamp-3 flex-1">
          {walkthrough.description}
        </p>

        {/* Topics */}
        <div className="flex flex-wrap gap-2 mb-4">
          {walkthrough.topics.slice(0, 3).map((topic) => (
            <span
              key={topic}
              className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded"
            >
              {topic}
            </span>
          ))}
          {walkthrough.topics.length > 3 && (
            <span className="px-2 py-1 text-xs text-gray-500 dark:text-gray-400">
              +{walkthrough.topics.length - 3} more
            </span>
          )}
        </div>

        {/* Footer with Time and Progress */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-800">
          <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{walkthrough.estimatedTime} min</span>
          </div>
          <div className={`text-sm font-medium ${progressColor}`}>
            {progressLabel}
          </div>
        </div>
      </div>
    </a>
  );
}
