import type { ContributorRole } from '@/lib/types';
import type { MemberRole } from './MembershipCard';
import { hasBuilderAccess, type SubscriptionAccessInfo } from '@/lib/entitlements';

/**
 * Derives the member's display role from authentication and profile signals.
 *
 * Priority:
 * 1. Admin (highest) — if isAdmin is true
 * 2. Contributor — if contributorRole is not null
 * 3. Student — if the subscription grants active Builder access AND the
 *    membership tier is STUDENT_BUILDER
 * 4. Builder — if the subscription grants active Builder access (any other
 *    Builder-equivalent tier, i.e. BUILDER)
 * 5. Free (default) — fallback for all other cases
 *
 * The Builder check uses the same source of truth as the navbar membership
 * badge (`hasBuilderAccess` against the /api/stripe/subscription response),
 * so the dashboard Membership card and the dropdown badge stay in sync.
 * `hasBuilderAccess` already denies non-active statuses (e.g. past_due), so a
 * past_due STUDENT_BUILDER subscriber falls through to 'free'.
 *
 * This function is total: it never throws and always returns a valid MemberRole.
 *
 * Requirements: 13.6
 */
export function deriveMemberRole(
  isAdmin: boolean,
  contributorRole: ContributorRole | null,
  subscription?: SubscriptionAccessInfo | null
): MemberRole {
  if (isAdmin) return 'admin';
  if (contributorRole) return 'contributor';
  if (hasBuilderAccess(subscription)) {
    if (subscription?.membership_tier === 'STUDENT_BUILDER') return 'student';
    return 'builder';
  }
  return 'free';
}
