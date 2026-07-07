'use client';

import { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { QuickLinkCard } from '@/components/ui/QuickLinkCard';
import { TestimonialForm } from '@/components/features/TestimonialForm';
import { apiClient } from '@/lib/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

interface DiscordStatus {
  connected: boolean;
  pending?: boolean;
  discord_username: string | null;
  discord_avatar_url: string | null;
  discord_display_name?: string | null;
  platform_state: string | null;
  last_synced_at: string | null;
  last_sync_status: string | null;
}

/**
 * Discord icon SVG component
 */
function DiscordIcon({ className = 'w-6 h-6' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
    </svg>
  );
}

/**
 * QuickLinksSection component displays the Community & Engagement section
 * with Discord connection integration and community participation cards.
 */
export function QuickLinksSection() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [showTestimonialModal, setShowTestimonialModal] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [discordStatus, setDiscordStatus] = useState<DiscordStatus | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);
  const [isDisconnecting, setIsDisconnecting] = useState(false);

  const fetchDiscordStatus = useCallback(async () => {
    try {
      const { data } = await apiClient.get<DiscordStatus>('/api/discord/status');
      if (data) {
        setDiscordStatus(data);
      }
    } catch {
      // Silently fail
    }
  }, []);

  useEffect(() => {
    fetchDiscordStatus();
  }, [fetchDiscordStatus]);

  // Show confirmation modal when ?discord=pending is in the URL
  useEffect(() => {
    if (searchParams.get('discord') === 'pending') {
      setShowConfirmModal(true);
    }
  }, [searchParams]);

  const handleConnectDiscord = () => {
    setIsConnecting(true);
    window.location.href = `${API_BASE_URL}/auth/discord/start`;
  };

  const handleConfirmIdentity = async () => {
    setIsConfirming(true);
    try {
      const { error } = await apiClient.post('/api/discord/confirm', {});
      if (!error) {
        await fetchDiscordStatus();
      }
    } catch {
      // Silently handle
    }
    setShowConfirmModal(false);
    setIsConfirming(false);
    router.replace('/dashboard');
  };

  const handleDisconnectAndChooseAnother = async () => {
    setIsDisconnecting(true);
    try {
      await apiClient.delete('/api/discord/disconnect');
    } catch {
      // Silently handle
    }
    setShowConfirmModal(false);
    setIsDisconnecting(false);
    router.replace('/dashboard');
    await fetchDiscordStatus();
  };

  return (
    <section className="w-full" aria-labelledby="quick-links-title">
      {/* Section Title */}
      <h2
        id="quick-links-title"
        className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6"
      >
        Community & Engagement
      </h2>

      {/* Quick Links Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Card 1: Discord Connection */}
        {discordStatus?.connected ? (
          <QuickLinkCard
            icon={<DiscordIcon className="w-6 h-6 text-[#5865F2]" />}
            label="Discord Connected"
            href="/settings/connected-accounts"
            ariaLabel="Discord connected - manage connection"
          />
        ) : (
          <QuickLinkCard
            icon={
              isConnecting ? (
                <svg className="w-6 h-6 animate-spin" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              ) : (
                <DiscordIcon className="w-6 h-6" />
              )
            }
            label={isConnecting ? "Connecting..." : "Connect Discord"}
            onClick={handleConnectDiscord}
            ariaLabel="Connect your Discord account for role sync"
          />
        )}

        {/* Card 2: Raise an Issue */}
        <QuickLinkCard
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          label="Raise an Issue"
          href="https://github.com/devsecblueprint/devsecblueprint/issues"
          external={true}
          ariaLabel="Raise an issue on GitHub (opens in new tab)"
        />

        {/* Card 3: Star on GitHub */}
        <QuickLinkCard
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
            </svg>
          }
          label="Star on GitHub"
          href="https://github.com/devsecblueprint/devsecblueprint"
          external={true}
          ariaLabel="Star the project on GitHub (opens in new tab)"
        />

        {/* Card 4: Share Your Success Story */}
        <QuickLinkCard
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
            </svg>
          }
          label="Share Your Success Story"
          onClick={() => setShowTestimonialModal(true)}
          ariaLabel="Share your success story (opens modal)"
        />

        {/* Card 5: Donate / Sponsor */}
        <QuickLinkCard
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
          }
          label="Donate"
          href="https://github.com/sponsors/devsecblueprint"
          external={true}
          ariaLabel="Sponsor the project on GitHub (opens in new tab)"
        />

        {/* Card 6: Merch Store */}
        <QuickLinkCard
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
            </svg>
          }
          label="Merch Store"
          href="https://shop.devsecblueprint.com/"
          external={true}
          ariaLabel="Visit the merch store (opens in new tab)"
        />
      </div>

      {/* Testimonial Form Modal */}
      <TestimonialForm isOpen={showTestimonialModal} onClose={() => setShowTestimonialModal(false)} />

      {/* Discord Identity Confirmation Modal */}
      {showConfirmModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white dark:bg-gray-900 rounded-xl shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Confirm Discord Account
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Is this the Discord account you want to link?
            </p>

            <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg mb-6">
              {discordStatus?.discord_avatar_url ? (
                <img
                  src={discordStatus.discord_avatar_url}
                  alt="Discord avatar"
                  className="w-10 h-10 rounded-full"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-[#5865F2] flex items-center justify-center">
                  <DiscordIcon className="w-5 h-5 text-white" />
                </div>
              )}
              <div>
                <p className="font-medium text-gray-900 dark:text-gray-100">
                  {discordStatus?.discord_username || 'Discord User'}
                </p>
                {discordStatus?.discord_display_name && discordStatus.discord_display_name !== discordStatus.discord_username && (
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {discordStatus.discord_display_name}
                  </p>
                )}
              </div>
            </div>

            <div className="flex flex-col gap-3">
              <button
                onClick={handleConfirmIdentity}
                disabled={isConfirming}
                className="w-full px-4 py-2.5 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900"
              >
                {isConfirming ? 'Confirming...' : 'Yes, this is my account'}
              </button>
              <button
                onClick={handleDisconnectAndChooseAnother}
                disabled={isDisconnecting}
                className="w-full px-4 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900"
              >
                {isDisconnecting ? 'Disconnecting...' : 'Disconnect & Choose Another'}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
