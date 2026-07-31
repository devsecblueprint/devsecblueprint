'use client';

import React, { Component, ReactNode } from 'react';
import { Card } from '@/components/ui/Card';

interface SectionErrorBoundaryProps {
  name: string;
  children: ReactNode;
}

interface SectionErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * Per-section Error Boundary for the Admin Dashboard.
 *
 * Wraps individual dashboard sections to isolate rendering failures.
 * A crash in one section does not prevent other sections from rendering.
 *
 * Requirements: 8.7
 */
export class SectionErrorBoundary extends Component<
  SectionErrorBoundaryProps,
  SectionErrorBoundaryState
> {
  constructor(props: SectionErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: Error): SectionErrorBoundaryState {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error(
      `[SectionErrorBoundary] "${this.props.name}" failed:`,
      error,
      errorInfo
    );
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <Card padding="md" className="border-red-200 dark:border-red-800">
          <div className="flex flex-col items-center justify-center py-6 text-center">
            <div className="text-red-500 dark:text-red-400 mb-4">
              <svg
                className="w-10 h-10 mx-auto"
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

            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Failed to load {this.props.name}
            </h3>

            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              An unexpected error occurred while rendering this section.
            </p>

            <button
              onClick={this.handleRetry}
              className="px-5 py-3 bg-amber-500 dark:bg-amber-400 text-gray-900 font-semibold rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-gray-950 min-h-[44px]"
              aria-label={`Retry loading ${this.props.name}`}
            >
              Retry
            </button>
          </div>
        </Card>
      );
    }

    return this.props.children;
  }
}
