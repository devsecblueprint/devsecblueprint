'use client';

import { useState } from 'react';
import { QuickLinkCard } from '@/components/ui/QuickLinkCard';
import { SuccessStoryModal } from '@/components/features/SuccessStoryModal';

/**
 * QuickLinksSection component displays the Community & Engagement section
 * with four interactive cards for community participation.
 * 
 * Validates Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 3.1, 4.1, 5.1, 5.2, 5.3
 */
export function QuickLinksSection() {
  const [showModal, setShowModal] = useState(false);

  const handleOpenModal = () => {
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
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
        {/* Card 1: Leave Feedback */}
        <QuickLinkCard
          icon={
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
          }
          label="Leave Feedback"
          href="https://discord.gg/SkYECC4TD8"
          external={true}
          ariaLabel="Leave feedback on Discord (opens in new tab)"
        />

        {/* Card 2: Raise an Issue */}
        <QuickLinkCard
          icon={
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
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
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
              />
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
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z"
              />
            </svg>
          }
          label="Share Your Success Story"
          onClick={handleOpenModal}
          ariaLabel="Share your success story (opens modal)"
        />
      </div>

      {/* Success Story Modal */}
      <SuccessStoryModal isOpen={showModal} onClose={handleCloseModal} />
    </section>
  );
}
