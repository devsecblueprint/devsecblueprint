'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

interface WelcomeModalProps {
  isOpen: boolean;
  onClose: () => void;
  username?: string;
}

export function WelcomeModal({ isOpen, onClose, username }: WelcomeModalProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (isOpen) {
      // Delay to trigger animation
      setTimeout(() => setIsVisible(true), 10);
    } else {
      setIsVisible(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div 
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 transition-opacity duration-300 ${
        isVisible ? 'opacity-100' : 'opacity-0'
      }`}
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
      
      {/* Modal */}
      <div 
        className={`relative w-full max-w-2xl max-h-[90vh] overflow-y-auto transform transition-all duration-300 ${
          isVisible ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        <Card padding="lg" className="m-2 sm:m-0">
          {/* Header */}
          <div className="text-center mb-4 sm:mb-6">
            <div className="mb-3 sm:mb-4">
              <svg 
                className="w-16 h-16 sm:w-20 sm:h-20 mx-auto text-amber-500 dark:text-amber-400" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" 
                />
              </svg>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              Welcome to The DevSec Blueprint{username ? `, ${username}` : ''}! 🎉
            </h2>
            <p className="text-base sm:text-lg text-gray-600 dark:text-gray-400">
              Your journey into DevSecOps and cloud security starts here
            </p>
          </div>

          {/* Content */}
          <div className="space-y-6 mb-6 sm:mb-8">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
              {/* Feature 1 */}
              <div className="text-center p-3 sm:p-4 rounded-lg bg-gray-50 dark:bg-gray-800/50">
                <div className="mb-2 sm:mb-3">
                  <svg 
                    className="w-10 h-10 sm:w-12 sm:h-12 mx-auto text-amber-500 dark:text-amber-400" 
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
                <h3 className="font-semibold text-sm sm:text-base text-gray-900 dark:text-gray-100 mb-1">
                  Track Progress
                </h3>
                <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                  Your progress is automatically saved as you complete lessons
                </p>
              </div>

              {/* Feature 2 */}
              <div className="text-center p-3 sm:p-4 rounded-lg bg-gray-50 dark:bg-gray-800/50">
                <div className="mb-2 sm:mb-3">
                  <svg 
                    className="w-10 h-10 sm:w-12 sm:h-12 mx-auto text-amber-500 dark:text-amber-400" 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path 
                      strokeLinecap="round" 
                      strokeLinejoin="round" 
                      strokeWidth={2} 
                      d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" 
                    />
                  </svg>
                </div>
                <h3 className="font-semibold text-sm sm:text-base text-gray-900 dark:text-gray-100 mb-1">
                  Project-Based Learning
                </h3>
                <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                  Build real security pipelines with capstone projects
                </p>
              </div>

              {/* Feature 3 */}
              <div className="text-center p-3 sm:p-4 rounded-lg bg-gray-50 dark:bg-gray-800/50">
                <div className="mb-2 sm:mb-3">
                  <svg 
                    className="w-10 h-10 sm:w-12 sm:h-12 mx-auto text-amber-500 dark:text-amber-400" 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path 
                      strokeLinecap="round" 
                      strokeLinejoin="round" 
                      strokeWidth={2} 
                      d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7" 
                    />
                  </svg>
                </div>
                <h3 className="font-semibold text-sm sm:text-base text-gray-900 dark:text-gray-100 mb-1">
                  Earn Badges
                </h3>
                <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                  Unlock achievements as you master security concepts
                </p>
              </div>

              {/* Feature 4 */}
              <div className="text-center p-3 sm:p-4 rounded-lg bg-gray-50 dark:bg-gray-800/50">
                <div className="mb-2 sm:mb-3">
                  <svg 
                    className="w-10 h-10 sm:w-12 sm:h-12 mx-auto text-amber-500 dark:text-amber-400" 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path 
                      strokeLinecap="round" 
                      strokeLinejoin="round" 
                      strokeWidth={2} 
                      d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" 
                    />
                  </svg>
                </div>
                <h3 className="font-semibold text-sm sm:text-base text-gray-900 dark:text-gray-100 mb-1">
                  Community Driven
                </h3>
                <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                  Join a community of security engineers and developers
                </p>
              </div>
            </div>

            {/* Getting Started */}
            <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-3 sm:p-4">
              <h3 className="font-semibold text-sm sm:text-base text-gray-900 dark:text-gray-100 mb-2 flex items-center">
                <svg 
                  className="w-4 h-4 sm:w-5 sm:h-5 mr-2 text-amber-500 dark:text-amber-400 flex-shrink-0" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
                  />
                </svg>
                Getting Started
              </h3>
              <p className="text-xs sm:text-sm text-gray-700 dark:text-gray-300">
                We recommend starting with the <strong>Prerequisites</strong> course to ensure you have 
                the foundational knowledge needed. Then explore other learning paths at your own pace.
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-col gap-2 sm:gap-3">
            <a
              href="/learn/welcome"
              className="inline-flex items-center justify-center px-4 sm:px-6 py-2.5 sm:py-3 text-sm sm:text-base bg-amber-500 dark:bg-amber-400 text-gray-900 font-semibold rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
              onClick={onClose}
            >
              <span>Read Welcome Message</span>
              <svg className="w-4 h-4 sm:w-5 sm:h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </a>
            <a
              href="/courses"
              className="inline-flex items-center justify-center px-4 sm:px-6 py-2.5 sm:py-3 text-sm sm:text-base bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 font-semibold rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
              onClick={onClose}
            >
              Explore All Courses
            </a>
          </div>
        </Card>
      </div>
    </div>
  );
}
