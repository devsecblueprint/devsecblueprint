'use client';

import { useEffect, useState } from 'react';
import { apiClient, RegistryStatusResponse } from '@/lib/api';
import { Spinner } from '@/components/ui/Spinner';
import { Badge } from '@/components/ui/Badge';
import { formatDistanceToNow } from 'date-fns';

interface RegistryStatusProps {
  className?: string;
}

export function RegistryStatus({ className = '' }: RegistryStatusProps) {
  const [status, setStatus] = useState<RegistryStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRegistryStatus();

    // Auto-refresh every 60 seconds
    const interval = setInterval(() => {
      fetchRegistryStatus();
    }, 60000);

    return () => clearInterval(interval);
  }, []);

  const fetchRegistryStatus = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const { data, error: apiError } = await apiClient.getRegistryStatus();

      if (apiError) {
        setError(apiError);
        return;
      }

      if (data) {
        setStatus(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch registry status');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetry = () => {
    fetchRegistryStatus();
  };

  // Loading state
  if (isLoading && !status) {
    return (
      <div className={className}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            Content Registry Status
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
            Content Registry Status
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
                Failed to Load Registry Status
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

  if (!status) {
    return null;
  }

  // Determine health color
  const isHealthy = status.status === 'healthy';
  const healthColor = isHealthy 
    ? 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
    : 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800';

  // Data state - Display registry status
  return (
    <div className={className}>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
        <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100">
          Content Registry Status
        </h2>
        <Badge 
          variant={isHealthy ? 'success' : 'warning'} 
          size="sm"
        >
          {status.status.charAt(0).toUpperCase() + status.status.slice(1)}
        </Badge>
      </div>

      <div className="space-y-4">
        {/* Health indicator */}
        <div className={`rounded-lg p-4 border ${healthColor}`}>
          <div className="flex items-center space-x-2">
            {isHealthy ? (
              <svg 
                className="w-5 h-5 flex-shrink-0" 
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
            ) : (
              <svg 
                className="w-5 h-5 flex-shrink-0" 
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
            )}
            <span className="text-sm font-medium">
              {isHealthy ? 'Registry is healthy and accessible' : 'Registry is unavailable'}
            </span>
          </div>
          {status.error && (
            <p className="text-sm mt-2 ml-7">
              {status.error}
            </p>
          )}
        </div>

        {/* Key metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 sm:p-4">
            <div className="text-xs text-gray-500 dark:text-gray-500 mb-1">
              Schema Version
            </div>
            <div className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100">
              {status.schema_version || 'N/A'}
            </div>
          </div>

          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 sm:p-4">
            <div className="text-xs text-gray-500 dark:text-gray-500 mb-1">
              Total Entries
            </div>
            <div className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100">
              {status.total_entries}
            </div>
          </div>

          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 sm:p-4">
            <div className="text-xs text-gray-500 dark:text-gray-500 mb-1">
              Last Updated
            </div>
            <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {status.last_updated 
                ? formatDistanceToNow(new Date(status.last_updated), { addSuffix: true })
                : 'N/A'
              }
            </div>
            {status.last_updated && (
              <div className="text-xs text-gray-500 dark:text-gray-500 mt-1 break-words">
                {new Date(status.last_updated).toLocaleString()}
              </div>
            )}
          </div>

          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 sm:p-4">
            <div className="text-xs text-gray-500 dark:text-gray-500 mb-1">
              Cache Status
            </div>
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                status.cache_status === 'loaded' 
                  ? 'bg-green-500' 
                  : status.cache_status === 'error'
                  ? 'bg-red-500'
                  : 'bg-gray-400'
              }`} />
              <span className="text-sm font-medium text-gray-900 dark:text-gray-100 capitalize">
                {status.cache_status.replace('_', ' ')}
              </span>
            </div>
            {status.cache_expires_in_seconds !== null && status.cache_expires_in_seconds > 0 && (
              <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                Expires in {Math.floor(status.cache_expires_in_seconds / 60)}m {status.cache_expires_in_seconds % 60}s
              </div>
            )}
          </div>
        </div>

        {/* S3 location */}
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
          <div className="text-xs text-gray-500 dark:text-gray-500 mb-2">
            S3 Location
          </div>
          <div className="text-sm font-mono text-gray-900 dark:text-gray-100 break-all">
            s3://{status.s3_bucket}/{status.s3_key}
          </div>
        </div>
      </div>
    </div>
  );
}
