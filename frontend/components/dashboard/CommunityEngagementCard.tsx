'use client';

import { useEffect, useState } from 'react';
import { QuickLinkCard } from '@/components/ui/QuickLinkCard';
import { TestimonialForm } from '@/components/features/TestimonialForm';
import { Card } from '@/components/ui/Card';
import { apiClient } from '@/lib/api';

/**
 * CommunityEngagementCard Component
 *
 * Consolidates all Community & Engagement actions into a single card with
 * a responsive 2-column grid (md+) / 1-column (mobile) of quick-link items.
 *
 * Requirements: 6.6
 */

export function CommunityEngagementCard() {
  const [showTestimonialModal, setShowTestimonialModal] = useState(false);
  const [testimonialStatus, setTestimonialStatus] = useState<'none' | 'pending' | 'approved'>('none');

  useEffect(() => {
    const fetchTestimonialStatus = async () => {
      try {
        const { data } = await apiClient.getMyTestimonial();
        if (data && data.status) {
          setTestimonialStatus(data.status as 'pending' | 'approved');
        }
      } catch {
        // No testimonial found (404) or error — stay at 'none'
      }
    };
    fetchTestimonialStatus();
  }, []);

  return (
    <Card className="h-full">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
        Community &amp; Engagement
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Raise an Issue */}
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

        {/* Share Your Success Story */}
        {testimonialStatus === 'none' ? (
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
        ) : (
          <button
            onClick={() => setShowTestimonialModal(true)}
            className={`flex flex-col items-center justify-center p-4 rounded-xl border-2 transition-colors min-h-[44px] min-w-[44px] w-full ${
              testimonialStatus === 'pending'
                ? 'border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-900/20'
                : 'border-green-300 dark:border-green-700 bg-green-50 dark:bg-green-900/20'
            }`}
            aria-label={testimonialStatus === 'pending' ? 'Your success story is pending review (click to edit)' : 'Your success story is live (click to view)'}
          >
            {/* Status icon */}
            {testimonialStatus === 'pending' ? (
              <svg className="w-6 h-6 text-amber-500 dark:text-amber-400 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            ) : (
              <svg className="w-6 h-6 text-green-500 dark:text-green-400 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}
            {/* Label */}
            <span className={`text-sm font-medium ${
              testimonialStatus === 'pending'
                ? 'text-amber-700 dark:text-amber-300'
                : 'text-green-700 dark:text-green-300'
            }`}>
              {testimonialStatus === 'pending' ? 'Story Pending' : 'Story Live ✓'}
            </span>
          </button>
        )}

        {/* Star on GitHub */}
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

        {/* Donate */}
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

        {/* Policies & Terms */}
        <QuickLinkCard
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          }
          label="Policies & Terms"
          href="https://drive.google.com/drive/folders/14st4E2pNmIImFmmOyaK0W2m5Pj6XI-Ey?usp=drive_link"
          external={true}
          ariaLabel="View policies and terms (opens in new tab)"
        />

        {/* Merch Store */}
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
      <TestimonialForm
        isOpen={showTestimonialModal}
        onClose={() => setShowTestimonialModal(false)}
      />
    </Card>
  );
}
