'use client';

import { useEffect, useState } from 'react';
import { apiClient, CapstoneSubmission } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { Spinner } from '@/components/ui/Spinner';
import { Badge } from '@/components/ui/Badge';
import { formatDistanceToNow } from 'date-fns';

interface CapstoneSubmissionsProps {
  className?: string;
}

// Map content_id to friendly capstone names
const getCapstoneTitle = (contentId: string): string => {
  const capstoneNames: Record<string, string> = {
    'devsecops-capstone': 'DevSecOps Capstone',
    'cloud_security_development-capstone': 'Cloud Security Development Capstone',
  };
  return capstoneNames[contentId] || contentId;
};

export function CapstoneSubmissions({ className = '' }: CapstoneSubmissionsProps) {
  const [submissions, setSubmissions] = useState<CapstoneSubmission[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page] = useState(1);
  const [pageSize] = useState(50);

  useEffect(() => {
    fetchSubmissions();
  }, [page, pageSize]);

  const fetchSubmissions = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const { data, error: apiError } = await apiClient.getCapstoneSubmissions(page, pageSize);

      if (apiError) {
        setError(apiError);
        return;
      }

      if (data) {
        setSubmissions(data.submissions);
        setTotalCount(data.total_count);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch submissions');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetry = () => {
    fetchSubmissions();
  };

  // Loading state
  if (isLoading) {
    return (
      <div className={className}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            Capstone Submissions
          </h2>
        </div>
        <div className="flex items-center justify-center py-12">
          <Spinner size="lg" />
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={className}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            Capstone Submissions
          </h2>
        </div>
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
          <div className="flex items-start space-x-3">
            <svg 
              className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
              />
            </svg>
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-red-900 dark:text-red-100 mb-1">
                Failed to Load Submissions
              </h3>
              <p className="text-sm text-red-800 dark:text-red-200 mb-3">
                {error}
              </p>
              <button
                onClick={handleRetry}
                className="text-sm font-medium text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Empty state
  if (submissions.length === 0) {
    return (
      <div className={className}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            Capstone Submissions
          </h2>
          <Badge variant="default" size="sm">
            {totalCount}
          </Badge>
        </div>
        <div className="text-center py-12">
          <svg 
            className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-600 mb-4" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" 
            />
          </svg>
          <p className="text-gray-600 dark:text-gray-400">
            No capstone submissions yet
          </p>
        </div>
      </div>
    );
  }

  // Data state - Display submissions in table layout
  return (
    <div className={className}>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
        <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100">
          Capstone Submissions
        </h2>
        <Badge variant="default" size="sm">
          {totalCount}
        </Badge>
      </div>

      {/* Desktop table view */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-800">
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-gray-100">
                User
              </th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-gray-100">
                Capstone
              </th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-gray-100">
                Repository
              </th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-gray-100">
                Submitted
              </th>
            </tr>
          </thead>
          <tbody>
            {submissions.map((submission) => (
              <tr 
                key={`${submission.user_id}-${submission.content_id}-${submission.submitted_at}`}
                className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
              >
                <td className="py-3 px-4">
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                        <span className="text-sm font-medium text-amber-600 dark:text-amber-400">
                          {submission.github_username.charAt(0).toUpperCase()}
                        </span>
                      </div>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {submission.github_username}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="py-3 px-4">
                  <div className="text-sm text-gray-900 dark:text-gray-100">
                    {getCapstoneTitle(submission.content_id)}
                  </div>
                </td>
                <td className="py-3 px-4">
                  <a
                    href={submission.repo_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-amber-600 dark:text-amber-400 hover:text-amber-700 dark:hover:text-amber-300 hover:underline inline-flex items-center space-x-1"
                  >
                    <span>{submission.repo_url.replace('https://github.com/', '')}</span>
                    <svg 
                      className="w-3 h-3" 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                    >
                      <path 
                        strokeLinecap="round" 
                        strokeLinejoin="round" 
                        strokeWidth={2} 
                        d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" 
                      />
                    </svg>
                  </a>
                </td>
                <td className="py-3 px-4">
                  <div className="text-sm text-gray-900 dark:text-gray-100">
                    {formatDistanceToNow(new Date(submission.submitted_at), { addSuffix: true })}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-500">
                    {new Date(submission.submitted_at).toLocaleDateString()}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile card view */}
      <div className="md:hidden space-y-3">
        {submissions.map((submission) => (
          <div
            key={`${submission.user_id}-${submission.content_id}-${submission.submitted_at}`}
            className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-3"
          >
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <div className="w-10 h-10 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                  <span className="text-base font-medium text-amber-600 dark:text-amber-400">
                    {submission.github_username.charAt(0).toUpperCase()}
                  </span>
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                  {submission.github_username}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-500">
                  {formatDistanceToNow(new Date(submission.submitted_at), { addSuffix: true })}
                </div>
              </div>
            </div>
            <div>
              <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                {getCapstoneTitle(submission.content_id)}
              </div>
              <a
                href={submission.repo_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-amber-600 dark:text-amber-400 hover:text-amber-700 dark:hover:text-amber-300 hover:underline inline-flex items-center space-x-1 break-all"
              >
                <span>{submission.repo_url.replace('https://github.com/', '')}</span>
                <svg 
                  className="w-3 h-3 flex-shrink-0" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" 
                  />
                </svg>
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
