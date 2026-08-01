import type { ContributorRole } from '@/lib/types';
import type { MemberRole } from './MembershipCard';

/**
 * Derives the member's display role from authentication and profile signals.
 *
 * Priority:
 * 1. Admin (highest) — if isAdmin is true
 * 2. Contributor — if contributorRole is not null
 * 3. Free (default) — fallback for all other cases
 *
 * Builder/Scholar detection is reserved for future subscription-based signals.
 * This function is total: it never throws and always returns a valid MemberRole.
 *
 * Requirements: 13.6
 */
export function deriveMemberRole(
  isAdmin: boolean,
  contributorRole: ContributorRole | null
): MemberRole {
  if (isAdmin) return 'admin';
  if (contributorRole) return 'contributor';
  return 'free';
}
