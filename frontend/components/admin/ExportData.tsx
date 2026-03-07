'use client';

import { useState } from 'react';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/Button';

export function ExportData() {
  const [isExporting, setIsExporting] = useState<string | null>(null);

  const handleExportUsers = async () => {
    setIsExporting('users');
    try {
      await apiClient.exportUsers();
    } catch (err) {
      console.error('Failed to export users:', err);
    } finally {
      setIsExporting(null);
    }
  };

  const handleExportSubmissions = async () => {
    setIsExporting('submissions');
    try {
      await apiClient.exportCapstoneSubmissions();
    } catch (err) {
      console.error('Failed to export submissions:', err);
    } finally {
      setIsExporting(null);
    }
  };

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
        Export Data
      </h2>
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
        Download platform data as CSV files for analysis and reporting.
      </p>

      <div className="space-y-4">
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">
                Export All Users
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                Download a CSV file containing all registered users with their statistics including completion rates, streaks, and quiz scores.
              </p>
              <div className="text-xs text-gray-500 dark:text-gray-500">
                Includes: user_id, username, github_username, registered_at, completed_count, overall_completion, current_streak, quizzes_passed
              </div>
            </div>
            <Button
              onClick={handleExportUsers}
              disabled={isExporting === 'users'}
              variant="secondary"
              size="sm"
              className="ml-4"
            >
              {isExporting === 'users' ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Exporting...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Export Users
                </>
              )}
            </Button>
          </div>
        </div>

        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">
                Export Capstone Submissions
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                Download a CSV file containing all capstone project submissions with repository URLs and submission timestamps.
              </p>
              <div className="text-xs text-gray-500 dark:text-gray-500">
                Includes: user_id, github_username, content_id, repo_url, submitted_at
              </div>
            </div>
            <Button
              onClick={handleExportSubmissions}
              disabled={isExporting === 'submissions'}
              variant="secondary"
              size="sm"
              className="ml-4"
            >
              {isExporting === 'submissions' ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Exporting...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Export Submissions
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
