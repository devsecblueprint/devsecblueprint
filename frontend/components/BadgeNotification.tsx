'use client';

import { useEffect, useState } from 'react';
import { Badge } from '@/lib/types';

interface BadgeNotificationProps {
  badge: Badge;
  onClose: () => void;
}

export function BadgeNotification({ badge, onClose }: BadgeNotificationProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    // Reset animation state when badge changes
    setIsVisible(false);
    setIsExiting(false);
    
    // Trigger entrance animation
    const showTimer = setTimeout(() => setIsVisible(true), 100);
    
    // Auto-dismiss after 3 seconds
    const dismissTimer = setTimeout(() => {
      handleClose();
    }, 3000);

    return () => {
      clearTimeout(showTimer);
      clearTimeout(dismissTimer);
    };
  }, [badge.id]); // Re-run when badge changes

  const handleClose = () => {
    setIsExiting(true);
    setTimeout(() => {
      setIsVisible(false);
      onClose();
    }, 300);
  };

  return (
    <div
      className={`fixed top-20 right-2 sm:right-4 left-2 sm:left-auto z-[100] transition-all duration-300 ${
        isVisible && !isExiting
          ? 'translate-x-0 opacity-100'
          : 'translate-x-full opacity-0'
      }`}
      role="alert"
      aria-live="polite"
    >
      <div className="bg-white dark:bg-gray-900 border-2 border-primary-400 rounded-lg shadow-2xl p-4 sm:p-6 max-w-sm mx-auto">
        {/* Header */}
        <div className="flex items-start justify-between mb-2 sm:mb-3">
          <div className="flex items-center space-x-2">
            <svg
              className="w-4 h-4 sm:w-5 sm:h-5 text-primary-500 flex-shrink-0"
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
            <h3 className="text-xs sm:text-sm font-semibold text-gray-900 dark:text-gray-100">
              Badge Earned!
            </h3>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors flex-shrink-0"
            aria-label="Close notification"
          >
            <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Badge Content */}
        <div className="flex items-center space-x-3 sm:space-x-4">
          {/* Badge Icon */}
          <div className="flex-shrink-0">
            <div className="w-12 h-12 sm:w-16 sm:h-16 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-2xl sm:text-3xl shadow-lg animate-bounce">
              {badge.icon}
            </div>
          </div>

          {/* Badge Info */}
          <div className="flex-1 min-w-0">
            <h4 className="text-base sm:text-lg font-bold text-gray-900 dark:text-gray-100 mb-0.5 sm:mb-1">
              {badge.title}
            </h4>
            <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
              {badge.description}
            </p>
          </div>
        </div>

        {/* Celebration Effect */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden rounded-lg">
          <div className="absolute top-0 left-1/4 w-1.5 h-1.5 sm:w-2 sm:h-2 bg-yellow-400 rounded-full animate-ping" style={{ animationDelay: '0ms' }} />
          <div className="absolute top-1/4 right-1/4 w-1.5 h-1.5 sm:w-2 sm:h-2 bg-primary-400 rounded-full animate-ping" style={{ animationDelay: '200ms' }} />
          <div className="absolute bottom-1/4 left-1/3 w-1.5 h-1.5 sm:w-2 sm:h-2 bg-green-400 rounded-full animate-ping" style={{ animationDelay: '400ms' }} />
        </div>
      </div>
    </div>
  );
}
