'use client';

import { MembershipCard, MemberRole } from '@/components/dashboard/MembershipCard';
import { DiscordConnectionCard } from '@/components/dashboard/DiscordConnectionCard';
import { CommunityEngagementCard } from '@/components/dashboard/CommunityEngagementCard';

/**
 * MembershipDiscordCommunitySection Component
 *
 * Two-column responsive layout wrapper that composes MembershipCard,
 * DiscordConnectionCard, and CommunityEngagementCard.
 *
 * Left column: Membership + Discord stacked (both short cards).
 * Right column: CommunityEngagementCard (taller, with 6 quick links).
 * Stacks to single column on mobile.
 *
 * Requirements: 6.1
 */

export interface MembershipDiscordCommunitySectionProps {
  role: MemberRole;
  isAdmin: boolean;
  /** Student Builder academic email, threaded to MembershipCard. */
  academicEmail?: string | null;
  /** Student Builder verification timestamp, threaded to MembershipCard. */
  verifiedAt?: string | null;
  /** Student Builder eligibility expiry, threaded to MembershipCard. */
  eligibilityExpiresAt?: string | null;
}

export function MembershipDiscordCommunitySection({
  role,
  isAdmin,
  academicEmail,
  verifiedAt,
  eligibilityExpiresAt,
}: MembershipDiscordCommunitySectionProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
      {/* Left column: Membership + Discord stacked */}
      <div className="flex flex-col gap-4 sm:gap-6">
        <MembershipCard
          role={role}
          isAdmin={isAdmin}
          academicEmail={academicEmail}
          verifiedAt={verifiedAt}
          eligibilityExpiresAt={eligibilityExpiresAt}
        />
        <DiscordConnectionCard />
      </div>
      {/* Right column: Community & Engagement */}
      <CommunityEngagementCard />
    </div>
  );
}
