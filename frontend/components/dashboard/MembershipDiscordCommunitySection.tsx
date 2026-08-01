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
}

export function MembershipDiscordCommunitySection({
  role,
  isAdmin,
}: MembershipDiscordCommunitySectionProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
      {/* Left column: Membership + Discord stacked */}
      <div className="flex flex-col gap-4 sm:gap-6">
        <MembershipCard role={role} isAdmin={isAdmin} />
        <DiscordConnectionCard />
      </div>
      {/* Right column: Community & Engagement */}
      <CommunityEngagementCard />
    </div>
  );
}
