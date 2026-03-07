'use client';

import { useEffect, useState } from 'react';
import { apiClient, ModuleHealthResponse } from '@/lib/api';
import { Spinner } from '@/components/ui/Spinner';
import { Badge } from '@/components/ui/Badge';

interface ModuleHealthProps {
  className?: string;
}

export function ModuleHealth({ className = '' }: ModuleHealthProps) {
  const [health, setHealth] = useState<ModuleHealthResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isErrorsExpanded, setIsErrorsExpanded] = useState(false);

  useEffect(() => {
    fetchModuleHealth();
  }, []);

  const fetchModuleHealth = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const { data, error: apiError } = await apiClient.getModuleHealth();

      if (apiError) {
        setError(apiError);
        return;
      }

      if (data) {
        setHealth(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch module health');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetry = () => {
    fetchModuleHealth();
  };

  // Loading state
  if (isLoading && !health) {
    return (
      <div className={className}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            Module Health
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
            Module Health
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
                Failed to Load Module Health
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

  if (!health) {
    return null;
  }

  // Determine health color based on validation percentage
  const getHealthColor = (percentage: number) => {
    if (percentage === 100) {
      return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800';
    } else if (percentage >= 90) {
      return 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800';
    } else {
      return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800';
    }
  };

  const getHealthBadgeVariant = (percentage: number): 'success' | 'warning' | 'default' => {
    if (percentage === 100) return 'success';
    if (percentage >= 90) return 'warning';
    return 'default';
  };

  const healthColor = getHealthColor(health.validation_pass_percentage);
  const badgeVariant = getHealthBadgeVariant(health.validation_pass_percentage);

  // Data state - Display module health metrics
  return (
    <div className={className}>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
        <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100">
          Module Health
        </h2>
        <Badge variant={badgeVariant} size="sm">
          {health.validation_pass_percentage.toFixed(1)}%
        </Badge>
      </div>

      <div className="space-y-4">
        {/* Validation percentage with progress bar */}
        <div className={`rounded-lg p-4 border ${healthColor}`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">
              Validation Pass Rate
            </span>
            <span className="text-sm font-semibold">
              {health.validation_pass_percentage.toFixed(1)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${
                health.validation_pass_percentage === 100
                  ? 'bg-green-600 dark:bg-green-400'
                  : health.validation_pass_percentage >= 90
                  ? 'bg-yellow-600 dark:bg-yellow-400'
                  : 'bg-red-600 dark:bg-red-400'
              }`}
              style={{ width: `${health.validation_pass_percentage}%` }}
            />
          </div>
          <div className="text-xs mt-2">
            {Math.round((health.validation_pass_percentage / 100) * health.total_modules)} of {health.total_modules} modules passing
          </div>
        </div>

        {/* Total modules metric */}
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 sm:p-4">
          <div className="text-xs text-gray-500 dark:text-gray-500 mb-1">
            Total Modules
          </div>
          <div className="text-xl sm:text-2xl font-semibold text-gray-900 dark:text-gray-100">
            {health.total_modules}
          </div>
        </div>

        {/* Content type breakdown in grid */}
        <div>
          <div className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
            Content by Type
          </div>
          <div className="grid grid-cols-2 gap-2 sm:gap-3">
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-2 sm:p-3">
              <div className="text-xs text-gray-500 dark:text-gray-500 mb-1">
                Quizzes
              </div>
              <div className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100">
                {health.content_by_type.quiz}
              </div>
            </div>

            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-2 sm:p-3">
              <div className="text-xs text-gray-500 dark:text-gray-500 mb-1">
                Modules
              </div>
              <div className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100">
                {health.content_by_type.module}
              </div>
            </div>

            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-2 sm:p-3">
              <div className="text-xs text-gray-500 dark:text-gray-500 mb-1">
                Capstones
              </div>
              <div className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100">
                {health.content_by_type.capstone}
              </div>
            </div>

            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-2 sm:p-3">
              <div className="text-xs text-gray-500 dark:text-gray-500 mb-1">
                Walkthroughs
              </div>
              <div className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100">
                {health.content_by_type.walkthrough}
              </div>
            </div>
          </div>
        </div>

        {/* Validation errors (if any) - Expandable section */}
        {health.validation_errors.length > 0 && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <button
              onClick={() => setIsErrorsExpanded(!isErrorsExpanded)}
              className="w-full flex items-center justify-between p-4 text-left hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors rounded-lg"
            >
              <div className="text-sm font-medium text-red-900 dark:text-red-100">
                Validation Errors ({health.validation_errors.length})
              </div>
              <svg
                className={`w-5 h-5 text-red-600 dark:text-red-400 transition-transform ${
                  isErrorsExpanded ? 'rotate-180' : ''
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>
            
            {isErrorsExpanded && (
              <div className="px-3 sm:px-4 pb-3 sm:pb-4">
                <div className="space-y-2 max-h-64 sm:max-h-96 overflow-y-auto">
                  {health.validation_errors.map((error, index) => (
                    <div 
                      key={`${error.module_id}-${index}`}
                      className="bg-white dark:bg-gray-900 rounded p-2 sm:p-3 text-xs"
                    >
                      <div className="font-mono text-red-600 dark:text-red-400 mb-1 break-all">
                        {error.module_id}
                      </div>
                      <div className="text-gray-700 dark:text-gray-300 break-words">
                        <span className="font-medium">{error.error_type}:</span> {error.error_message}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
