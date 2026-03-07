'use client';

import React, { Component, ReactNode } from 'react';
import { Card } from '@/components/ui/Card';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * Error Boundary Component
 * 
 * Catches React rendering errors and displays a user-friendly error message
 * with options to retry or navigate back.
 * 
 * Requirements: 17.1, 17.5
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null
    };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null
    });
  };

  handleGoBack = () => {
    window.history.back();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex items-center justify-center p-4">
          <Card padding="lg" className="max-w-2xl w-full">
            <div className="text-center py-8">
              <div className="text-red-500 dark:text-red-400 mb-6">
                <svg 
                  className="w-20 h-20 mx-auto" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" 
                  />
                </svg>
              </div>
              
              <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-3">
                Something Went Wrong
              </h2>
              
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                We encountered an unexpected error while displaying this page.
                {this.state.error && (
                  <span className="block mt-2 text-sm font-mono text-gray-500 dark:text-gray-500">
                    {this.state.error.message}
                  </span>
                )}
              </p>
              
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <button
                  onClick={this.handleReset}
                  className="px-6 py-3 bg-amber-500 dark:bg-amber-400 text-gray-900 font-semibold rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500"
                  aria-label="Try again"
                >
                  Try Again
                </button>
                
                <button
                  onClick={this.handleGoBack}
                  className="px-6 py-3 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 font-semibold rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500"
                  aria-label="Go back"
                >
                  Go Back
                </button>
              </div>
            </div>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}
