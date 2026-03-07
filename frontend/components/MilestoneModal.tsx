'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

interface MilestoneModalProps {
  isOpen: boolean;
  onClose: () => void;
  score: number;
}

export function MilestoneModal({ isOpen, onClose, score }: MilestoneModalProps) {
  const isPerfectScore = score === 100;
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
        className={`relative w-full max-w-md transform transition-all duration-300 ${
          isVisible ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        <Card padding="lg">
          {/* Header */}
          <div className="text-center mb-6">
            <div className="mb-4">
              <svg 
                className="w-16 h-16 mx-auto text-amber-500 dark:text-amber-400" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" 
                />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              {isPerfectScore ? 'Perfect Score!' : 'Module Completed'}
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-400">
              {isPerfectScore 
                ? 'Outstanding! You achieved a perfect score on this module!' 
                : 'Great work on completing this module!'}
            </p>
          </div>

          {/* Content */}
          <div className="mb-6">
            {/* Score Display */}
            <div className="text-center p-6 rounded-lg bg-gray-50 dark:bg-gray-800/50">
              <div className="text-5xl font-bold text-amber-500 dark:text-amber-400 mb-2">
                {score}%
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Your Score
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-center">
            <Button
              variant="primary"
              onClick={onClose}
              className="px-8 py-3"
            >
              Continue Learning
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
