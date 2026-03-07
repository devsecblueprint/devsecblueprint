/**
 * Admin Reset Button Component
 * 
 * Provides a button for admin users to reset their progress.
 * Only visible to user "damienjburks".
 */

'use client';

import React, { useState } from 'react';
import { useAuth } from '@/lib/hooks/useAuth';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';

const ADMIN_USERS = ['damienjburks', 'iqtheengineer', 'thogue12'];

export function AdminResetButton() {
  const { username } = useAuth();
  const [isResetting, setIsResetting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Only show for admin users
  if (!username || !ADMIN_USERS.includes(username)) {
    return null;
  }

  const handleReset = async () => {
    setIsResetting(true);
    setError(null);

    try {
      const { data, error } = await apiClient.resetProgress();

      if (error) {
        setError(error);
        setIsResetting(false);
        return;
      }

      // Log out the user to clear session
      await apiClient.logout();
      
      // Clear session storage
      sessionStorage.clear();
      
      // Redirect to home page
      window.location.href = '/';
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset progress');
      setIsResetting(false);
    }
  };

  if (showConfirm) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <svg 
            className="w-6 h-6 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" 
            />
          </svg>
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-red-900 dark:text-red-100 mb-1">
              Confirm Progress Reset
            </h3>
            <p className="text-sm text-red-800 dark:text-red-200 mb-4">
              This will permanently delete all your progress data. This action cannot be undone.
            </p>
            <div className="flex items-center space-x-3">
              <Button
                onClick={handleReset}
                disabled={isResetting}
                variant="danger"
                size="sm"
              >
                {isResetting ? (
                  <>
                    <Spinner size="sm" className="mr-2" />
                    Resetting...
                  </>
                ) : (
                  'Yes, Reset All Progress'
                )}
              </Button>
              <Button
                onClick={() => {
                  setShowConfirm(false);
                  setError(null);
                }}
                disabled={isResetting}
                variant="secondary"
                size="sm"
              >
                Cancel
              </Button>
            </div>
            {error && (
              <p className="mt-3 text-sm text-red-700 dark:text-red-300">
                Error: {error}
              </p>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
      <div className="flex items-start space-x-3">
        <svg 
          className="w-6 h-6 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" 
          />
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" 
          />
        </svg>
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-yellow-900 dark:text-yellow-100 mb-1">
            Admin Controls
          </h3>
          <p className="text-sm text-yellow-800 dark:text-yellow-200 mb-3">
            Reset all your progress data to start fresh. This is useful for testing.
          </p>
          <Button
            onClick={() => setShowConfirm(true)}
            variant="secondary"
            size="sm"
          >
            Reset All Progress
          </Button>
        </div>
      </div>
    </div>
  );
}
