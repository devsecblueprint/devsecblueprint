'use client';

import { useState } from 'react';
import { apiClient } from '@/lib/api';

export interface CertificateDownloadProps {
  pathway_id: string;
  disabled: boolean;
}

export function CertificateDownload({
  pathway_id,
  disabled,
}: CertificateDownloadProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDownload() {
    if (disabled || isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.get<{ download_url: string }>(
        `/certifications/${encodeURIComponent(pathway_id)}/credential/download`
      );

      if (response.error) {
        setError(response.error);
        return;
      }

      if (response.data?.download_url) {
        window.open(response.data.download_url, '_blank', 'noopener,noreferrer');
      }
    } catch {
      setError('Failed to fetch download URL. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="relative inline-block">
        <button
          onClick={handleDownload}
          disabled={disabled || isLoading}
          className="inline-flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-3 text-sm font-semibold text-gray-900 transition-colors hover:bg-amber-600 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-amber-400 dark:hover:bg-amber-500 dark:focus:ring-offset-gray-950 min-h-[44px]"
          aria-label={
            disabled
              ? 'Certificate download unavailable — certificate not yet generated'
              : isLoading
                ? 'Downloading certificate...'
                : 'Download certificate PDF'
          }
          title={disabled ? 'Certificate not yet generated' : undefined}
        >
          {isLoading ? (
            <svg
              className="h-4 w-4 animate-spin"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          ) : (
            <svg
              className="h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
              />
            </svg>
          )}
          {isLoading ? 'Downloading...' : 'Download Certificate'}
        </button>
      </div>
      {error && (
        <p className="text-sm text-red-600 dark:text-red-400" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
