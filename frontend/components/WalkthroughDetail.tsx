'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useRef } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { READMERenderer } from '@/components/READMERenderer';
import type { WalkthroughDetail as WalkthroughDetailType } from '@/lib/types';

export interface WalkthroughDetailProps {
  walkthrough: WalkthroughDetailType;
  onMarkComplete: () => void;
}

export function WalkthroughDetail({ walkthrough, onMarkComplete }: WalkthroughDetailProps) {
  const router = useRouter();
  const mainHeadingRef = useRef<HTMLHeadingElement>(null);

  // Focus management: focus on main heading when component mounts
  useEffect(() => {
    if (mainHeadingRef.current) {
      mainHeadingRef.current.focus();
    }
  }, []);

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'Beginner':
        return 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 border-green-300 dark:border-green-700';
      case 'Intermediate':
        return 'bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-300 border-amber-300 dark:border-amber-700';
      case 'Advanced':
        return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 border-red-300 dark:border-red-700';
      default:
        return 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300 border-gray-300 dark:border-gray-700';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 border-green-300 dark:border-green-700';
      case 'in_progress':
        return 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 border-blue-300 dark:border-blue-700';
      default:
        return 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300 border-gray-300 dark:border-gray-700';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'not_started':
        return 'Not Started';
      case 'in_progress':
        return 'In Progress';
      case 'completed':
        return 'Completed';
      default:
        return status;
    }
  };

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <button
        onClick={() => router.push('/walkthroughs')}
        className="inline-flex items-center text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
        aria-label="Back to walkthroughs"
      >
        <svg 
          className="w-5 h-5 mr-2" 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M10 19l-7-7m0 0l7-7m-7 7h18" 
          />
        </svg>
        Back to Walkthroughs
      </button>

      {/* Header */}
      <div>
        {/* Status Badges */}
        <div className="flex flex-wrap items-center gap-3 mb-4">
          <span 
            className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getDifficultyColor(walkthrough.difficulty)}`}
            aria-label={`Difficulty: ${walkthrough.difficulty}`}
          >
            {walkthrough.difficulty}
          </span>
          <span 
            className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(walkthrough.progress.status)}`}
            aria-label={`Status: ${getStatusLabel(walkthrough.progress.status)}`}
          >
            {getStatusLabel(walkthrough.progress.status)}
          </span>
          <span className="text-sm text-gray-600 dark:text-gray-400">
            <svg 
              className="w-4 h-4 inline mr-1" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" 
              />
            </svg>
            {walkthrough.estimatedTime} minutes
          </span>
        </div>

        {/* Title and Description */}
        <h1 
          ref={mainHeadingRef}
          tabIndex={-1}
          className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4 focus:outline-none"
        >
          {walkthrough.title}
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400 mb-6">
          {walkthrough.description}
        </p>

        {/* Topics */}
        <div className="flex flex-wrap gap-2 mb-6" role="list" aria-label="Topics">
          {walkthrough.topics.map((topic) => (
            <Badge key={topic} variant="default" size="sm">
              {topic}
            </Badge>
          ))}
        </div>

        {/* Authors */}
        {walkthrough.authors && walkthrough.authors.length > 0 && (
          <Card padding="md" className="mb-6">
            <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2">
              {walkthrough.authors.length === 1 ? 'Author' : 'Authors'}
            </h2>
            <div className="flex flex-wrap gap-2">
              {walkthrough.authors.map((author, index, authors) => (
                <span key={index} className="text-sm text-gray-600 dark:text-gray-400">
                  {author.url ? (
                    <a
                      href={author.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary-600 dark:text-primary-400 hover:underline"
                    >
                      {author.name}
                    </a>
                  ) : (
                    author.name
                  )}
                  {index < authors.length - 1 && ', '}
                </span>
              ))}
            </div>
          </Card>
        )}

        {/* Prerequisites */}
        {walkthrough.prerequisites.length > 0 && (
          <Card padding="md" className="mb-6">
            <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Prerequisites
            </h2>
            <ul className="list-disc list-inside space-y-1">
              {walkthrough.prerequisites.map((prereq) => (
                <li key={prereq} className="text-sm text-gray-600 dark:text-gray-400">
                  {prereq}
                </li>
              ))}
            </ul>
          </Card>
        )}

        {/* Action Buttons */}
        {walkthrough.repositoryUrl && (
          <div className="flex flex-wrap gap-3">
            <a
              href={walkthrough.repositoryUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-6 py-3 bg-amber-500 dark:bg-amber-400 text-gray-900 font-semibold rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500"
              aria-label="View walkthrough code on GitHub"
            >
              <svg 
                className="w-5 h-5 mr-2" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" 
                />
              </svg>
              View Code
            </a>
          </div>
        )}
      </div>

      {/* README Content */}
      <Card padding="lg">
        {walkthrough.readme ? (
          <READMERenderer 
            markdown={walkthrough.readme} 
            walkthroughId={walkthrough.id}
          />
        ) : (
          <div className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <svg 
                className="w-16 h-16 mx-auto" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" 
                />
              </svg>
            </div>
            <p className="text-gray-600 dark:text-gray-400">
              Documentation not available for this walkthrough.
            </p>
          </div>
        )}
      </Card>

      {/* Progress Timestamps */}
      {(walkthrough.progress.startedAt || walkthrough.progress.completedAt) && (
        <Card padding="md">
          <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
            Progress
          </h2>
          <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
            {walkthrough.progress.startedAt && (
              <div>
                <span className="font-medium">Started:</span>{' '}
                {new Date(walkthrough.progress.startedAt).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </div>
            )}
            {walkthrough.progress.completedAt && (
              <div>
                <span className="font-medium">Completed:</span>{' '}
                {new Date(walkthrough.progress.completedAt).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Mark as Complete Button - Bottom Left */}
      {walkthrough.progress.status === 'in_progress' && (
        <div className="flex justify-start">
          <button
            onClick={onMarkComplete}
            className="inline-flex items-center px-6 py-3 bg-green-500 dark:bg-green-600 text-white font-semibold rounded-lg hover:bg-green-600 dark:hover:bg-green-700 transition-colors focus:outline-none focus:ring-2 focus:ring-green-500"
            aria-label="Mark walkthrough as complete"
          >
            <svg 
              className="w-5 h-5 mr-2" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M5 13l4 4L19 7" 
              />
            </svg>
            Mark as Complete
          </button>
        </div>
      )}
    </div>
  );
}
