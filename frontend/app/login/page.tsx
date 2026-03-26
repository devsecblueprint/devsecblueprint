'use client';

import { useState } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api';
import { Spinner } from '@/components/ui/Spinner';

export default function LoginPage() {
  const [loadingProvider, setLoadingProvider] = useState<'github' | 'gitlab' | null>(null);

  const handleLogin = (provider: 'github' | 'gitlab') => {
    setLoadingProvider(provider);
    window.location.href =
      provider === 'github'
        ? apiClient.getAuthStartUrl()
        : apiClient.getGitLabAuthStartUrl();
  };

  const isLoading = loadingProvider !== null;

  return (
    <main className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <div className="max-w-md w-full space-y-8 p-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white mb-8">
            Login to The DevSec Blueprint
          </h1>

          <div className="space-y-3">
            {/* GitHub button */}
            <button
              onClick={() => handleLogin('github')}
              disabled={isLoading}
              aria-label="Login with GitHub"
              className="w-full flex items-center justify-center gap-3 px-6 py-3 rounded-lg text-white font-semibold transition-opacity focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ backgroundColor: '#24292e' }}
            >
              {loadingProvider === 'github' ? (
                <>
                  <Spinner size="sm" />
                  <span>Redirecting...</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                  </svg>
                  <span>Login with GitHub</span>
                </>
              )}
            </button>

            {/* GitLab button */}
            <button
              onClick={() => handleLogin('gitlab')}
              disabled={isLoading}
              aria-label="Login with GitLab"
              className="w-full flex items-center justify-center gap-3 px-6 py-3 rounded-lg text-white font-semibold transition-opacity focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-400 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ backgroundColor: '#FC6D26' }}
            >
              {loadingProvider === 'gitlab' ? (
                <>
                  <Spinner size="sm" />
                  <span>Redirecting...</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 512 512" aria-hidden="true">
                    <path d="M503.5 204.6L502.8 202.8L433.1 21C431.7 17.5 429.2 14.4 425.9 12.4C422.8 10.4 419.3 9.4 415.8 9.4C412.2 9.4 408.7 10.5 405.7 12.6C402.6 14.7 400.3 17.7 399 21.2L347.2 168.2H164.8L113 21.2C111.7 17.7 109.4 14.7 106.3 12.6C103.3 10.5 99.8 9.4 96.2 9.4C92.7 9.4 89.2 10.4 86.1 12.4C82.8 14.4 80.3 17.5 78.9 21L9.2 202.8L8.5 204.6C-1.5 230.8-2.7 259.6 5 286.3C12.6 313 29.1 336.3 51.7 352.6L52.7 353.3L55.7 355.5L163.3 434.4L216.4 473.2L248.4 496.5C253.3 500.2 258.6 502 264 502C269.4 502 274.7 500.2 279.6 496.5L311.6 473.2L364.7 434.4L459.3 353.3L460.3 352.6C482.9 336.3 499.4 313 507 286.3C514.7 259.6 513.5 230.8 503.5 204.6Z" />
                  </svg>
                  <span>Login with GitLab</span>
                </>
              )}
            </button>
          </div>

          <Link
            href="/"
            className="inline-block mt-6 text-primary-400 hover:text-primary-300 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-400 rounded px-2 py-1"
          >
            Back to Home
          </Link>
        </div>
      </div>
    </main>
  );
}
