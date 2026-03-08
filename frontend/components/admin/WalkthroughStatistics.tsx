'use client';

import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { Spinner } from '@/components/ui/Spinner';

interface WalkthroughStatisticsData {
  completed_count: number;
  in_progress_count: number;
  most_popular_walkthrough: string | null;
}

// Walkthrough ID to title mapping
const WALKTHROUGH_TITLES: Record<string, string> = {
  'aws-detective-control': 'Event-Driven S3 Public Access Detective Control',
  'devsecops-home-lab': 'DevSecOps Home Lab: From Scratch to CI/CD',
  'devsecops-pipeline-aws': 'Cloud Native DevSecOps Pipeline on AWS',
  'devsecops-pipeline-azure': 'Cloud-Native DevSecOps Pipeline on Azure',
  'devsecops-pipeline-gcp': 'Cloud Native DevSecOps Pipeline on GCP',
  'devsecops-pipeline-gha': 'GitHub Actions DevSecOps Pipeline',
};

export function WalkthroughStatistics() {
  const [data, setData] = useState<WalkthroughStatisticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStatistics();
  }, []);

  const fetchStatistics = async () => {
    setLoading(true);
    setError(null);

    try {
      const { data: responseData, error: apiError } = await apiClient.getWalkthroughStatistics();

      if (apiError) {
        setError(apiError);
        return;
      }

      if (responseData) {
        setData(responseData);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch statistics');
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    fetchStatistics();
  };

  // Get walkthrough title from ID
  const getWalkthroughTitle = (id: string | null): string => {
    if (!id) return 'No data available';
    return WALKTHROUGH_TITLES[id] || id;
  };

  // Loading state
  if (loading) {
    return (
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Walkthrough Statistics
        </h2>
        <div className="flex items-center justify-center py-12">
          <Spinner size="lg" />
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Walkthrough Statistics
        </h2>
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
                Failed to Load Statistics
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

  // Data state - Display statistics in grid layout
  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
        Walkthrough Statistics
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Completed Walkthroughs Card */}
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                Completed
              </p>
              <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                {data?.completed_count ?? 0}
              </p>
            </div>
            <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
              <svg 
                className="w-6 h-6 text-green-600 dark:text-green-400" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" 
                />
              </svg>
            </div>
          </div>
        </div>

        {/* In-Progress Walkthroughs Card */}
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                In Progress
              </p>
              <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                {data?.in_progress_count ?? 0}
              </p>
            </div>
            <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
              <svg 
                className="w-6 h-6 text-blue-600 dark:text-blue-400" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M13 10V3L4 14h7v7l9-11h-7z" 
                />
              </svg>
            </div>
          </div>
        </div>

        {/* Most Popular Walkthrough Card */}
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                Most Popular
              </p>
              {data?.most_popular_walkthrough ? (
                <p className="text-lg font-bold text-gray-900 dark:text-gray-100 break-words leading-tight">
                  {getWalkthroughTitle(data.most_popular_walkthrough)}
                </p>
              ) : (
                <p className="text-sm text-gray-500 dark:text-gray-500">
                  No data available
                </p>
              )}
            </div>
            <div className="w-12 h-12 bg-amber-100 dark:bg-amber-900/30 rounded-lg flex items-center justify-center flex-shrink-0">
              <svg 
                className="w-6 h-6 text-amber-600 dark:text-amber-400" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" 
                />
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
