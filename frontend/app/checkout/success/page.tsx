'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { Footer } from '@/components/layout/Footer';
import { AuthGuard } from '@/components/AuthGuard';
import { apiClient } from '@/lib/api';

interface DiscordStatus {
  connected: boolean;
  discord_username: string | null;
  discord_avatar_url: string | null;
  platform_state: string | null;
  last_synced_at: string | null;
  last_sync_status: string | null;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

export default function CheckoutSuccessPage() {
  const [discordStatus, setDiscordStatus] = useState<DiscordStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showConfetti, setShowConfetti] = useState(true);

  useEffect(() => {
    async function fetchDiscordStatus() {
      const { data } = await apiClient.get<DiscordStatus>('/api/discord/status');
      if (data) {
        setDiscordStatus(data);
      }
      setIsLoading(false);
    }

    fetchDiscordStatus();

    // Hide confetti after 5 seconds
    const timer = setTimeout(() => setShowConfetti(false), 5000);
    return () => clearTimeout(timer);
  }, []);

  const handleConnectDiscord = () => {
    window.location.href = `${API_BASE_URL}/auth/discord/start`;
  };

  return (
    <AuthGuard>
      <div className="min-h-screen bg-white dark:bg-gray-950 flex flex-col relative overflow-hidden">
        <NavbarWithAuth />

        {/* CSS Confetti Animation */}
        {showConfetti && (
          <div className="fixed inset-0 pointer-events-none z-50" aria-hidden="true">
            {[...Array(50)].map((_, i) => (
              <div
                key={i}
                className="confetti-piece"
                style={{
                  left: `${Math.random() * 100}%`,
                  animationDelay: `${Math.random() * 3}s`,
                  animationDuration: `${2 + Math.random() * 3}s`,
                  // @ts-expect-error CSS custom property
                  '--drift': `${(Math.random() - 0.5) * 160}px`,
                  backgroundColor: ['#f59e0b', '#3b82f6', '#8b5cf6', '#10b981', '#ef4444', '#ec4899'][
                    Math.floor(Math.random() * 6)
                  ],
                }}
              />
            ))}
          </div>
        )}

        <main className="flex-1 pt-16 flex items-center justify-center">
          <div className="max-w-lg mx-auto px-4 sm:px-6 py-12 text-center">
            {/* Success Icon */}
            <div className="mb-6">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-100 dark:bg-green-900/30">
                <svg
                  className="w-10 h-10 text-green-600 dark:text-green-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
            </div>

            {/* Main Message */}
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4">
              {discordStatus?.connected
                ? 'Congratulations on your membership!'
                : 'Payment Successful!'}
            </h1>

            <p className="text-lg text-gray-600 dark:text-gray-400 mb-8">
              {discordStatus?.connected
                ? "Your subscription is active and your Discord role will be synced shortly."
                : "Your subscription is now active. Connect your Discord to receive your full benefits."}
            </p>

            {/* Discord CTA */}
            {isLoading ? (
              <div className="animate-pulse mb-8">
                <div className="h-14 w-64 mx-auto bg-gray-200 dark:bg-gray-700 rounded-lg" />
              </div>
            ) : !discordStatus?.connected ? (
              <div className="mb-8 p-6 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-2xl">
                <div className="flex items-center justify-center mb-3">
                  <svg className="w-8 h-8 text-indigo-600 dark:text-indigo-400" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                    <path d="M20.317 4.37a19.791 19.791 0 00-4.885-1.515.074.074 0 00-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 00-5.487 0 12.64 12.64 0 00-.617-1.25.077.077 0 00-.079-.037A19.736 19.736 0 003.677 4.37a.07.07 0 00-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 00.031.057 19.9 19.9 0 005.993 3.03.078.078 0 00.084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 00-.041-.106 13.107 13.107 0 01-1.872-.892.077.077 0 01-.008-.128 10.2 10.2 0 00.372-.292.074.074 0 01.077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 01.078.01c.12.098.246.198.373.292a.077.077 0 01-.006.127 12.299 12.299 0 01-1.873.892.077.077 0 00-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 00.084.028 19.839 19.839 0 006.002-3.03.077.077 0 00.032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 00-.031-.03z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  Join the Discord
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  Connect your Discord account to receive your membership role and access exclusive channels.
                </p>
                <button
                  onClick={handleConnectDiscord}
                  className="inline-flex items-center justify-center px-6 py-3 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
                >
                  <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                    <path d="M20.317 4.37a19.791 19.791 0 00-4.885-1.515.074.074 0 00-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 00-5.487 0 12.64 12.64 0 00-.617-1.25.077.077 0 00-.079-.037A19.736 19.736 0 003.677 4.37a.07.07 0 00-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 00.031.057 19.9 19.9 0 005.993 3.03.078.078 0 00.084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 00-.041-.106 13.107 13.107 0 01-1.872-.892.077.077 0 01-.008-.128 10.2 10.2 0 00.372-.292.074.074 0 01.077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 01.078.01c.12.098.246.198.373.292a.077.077 0 01-.006.127 12.299 12.299 0 01-1.873.892.077.077 0 00-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 00.084.028 19.839 19.839 0 006.002-3.03.077.077 0 00.032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 00-.031-.03z" />
                  </svg>
                  Connect Discord
                </button>
              </div>
            ) : (
              <div className="mb-8 p-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-2xl">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="font-medium text-green-700 dark:text-green-300">
                    Discord Connected
                  </span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Connected as <span className="font-medium">{discordStatus.discord_username}</span>. Your role will sync automatically.
                </p>
              </div>
            )}

            {/* Back to Dashboard */}
            <Link
              href="/dashboard"
              className="inline-flex items-center justify-center px-6 py-3 rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 font-semibold hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950"
            >
              Go to Dashboard
              <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </Link>
          </div>
        </main>

        <Footer variant="minimal" />

        {/* Confetti CSS */}
        <style jsx global>{`
          @keyframes confetti-fall {
            0% {
              opacity: 1;
              top: -10px;
              transform: translateX(0) rotate(0deg);
            }
            50% {
              opacity: 1;
            }
            100% {
              opacity: 0;
              top: 100vh;
              transform: translateX(var(--drift, 40px)) rotate(720deg);
            }
          }

          .confetti-piece {
            position: fixed;
            top: -10px;
            width: 10px;
            height: 10px;
            opacity: 0;
            animation: confetti-fall linear forwards;
          }

          .confetti-piece:nth-child(odd) {
            border-radius: 50%;
          }

          .confetti-piece:nth-child(even) {
            border-radius: 2px;
          }
        `}</style>
      </div>
    </AuthGuard>
  );
}
