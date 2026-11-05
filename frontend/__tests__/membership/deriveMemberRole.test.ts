/**
 * deriveMemberRole — subscription-tier cases for Student Builder.
 *
 * Complements frontend/__tests__/deriveMemberRole.test.ts (which covers the
 * admin/contributor/free branches) by exercising the subscription-driven
 * student vs builder resolution added for the Student Builder membership.
 *
 * Priority under test:
 *   admin > contributor > student (active STUDENT_BUILDER) > builder (active
 *   BUILDER) > free. hasBuilderAccess denies non-active statuses, so a
 *   past_due student falls through to 'free'.
 */

import { deriveMemberRole } from '@/components/dashboard/utils';
import type { ContributorRole } from '@/lib/types';
import type { SubscriptionAccessInfo } from '@/lib/entitlements';

describe('deriveMemberRole — subscription tiers', () => {
  const contributorRole: ContributorRole = {
    role: 'contributor',
    assigned_by: 'admin-user',
    assigned_at: '2024-01-01T00:00:00Z',
    note: 'Active contributor',
  };

  const activeStudent: SubscriptionAccessInfo = {
    membership_tier: 'STUDENT_BUILDER',
    subscription_status: 'active',
  };

  const activeBuilder: SubscriptionAccessInfo = {
    membership_tier: 'BUILDER',
    subscription_status: 'active',
  };

  const pastDueStudent: SubscriptionAccessInfo = {
    membership_tier: 'STUDENT_BUILDER',
    subscription_status: 'past_due',
  };

  it("returns 'student' for an active STUDENT_BUILDER subscriber", () => {
    expect(deriveMemberRole(false, null, activeStudent)).toBe('student');
  });

  it("returns 'builder' for an active BUILDER subscriber", () => {
    expect(deriveMemberRole(false, null, activeBuilder)).toBe('builder');
  });

  it("returns 'contributor' when a contributor also has an active student sub", () => {
    expect(deriveMemberRole(false, contributorRole, activeStudent)).toBe('contributor');
  });

  it("returns 'admin' regardless of subscription tier", () => {
    expect(deriveMemberRole(true, null, activeStudent)).toBe('admin');
    expect(deriveMemberRole(true, contributorRole, activeBuilder)).toBe('admin');
  });

  it("returns 'free' for a past_due STUDENT_BUILDER subscriber (access denied)", () => {
    expect(deriveMemberRole(false, null, pastDueStudent)).toBe('free');
  });

  it("returns 'free' when there is no subscription", () => {
    expect(deriveMemberRole(false, null, null)).toBe('free');
    expect(deriveMemberRole(false, null, undefined)).toBe('free');
  });
});
