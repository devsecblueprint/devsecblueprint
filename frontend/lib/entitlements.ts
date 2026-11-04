/**
 * Client-side entitlement helpers.
 *
 * These mirror the backend access rules so the UI does not grant access the
 * server will deny. The source of truth for access is always the backend; this
 * only keeps the UI consistent.
 */

/** Subset of the /api/stripe/subscription response needed for access checks. */
export interface SubscriptionAccessInfo {
  membership_tier?: string | null;
  subscription_status?: string | null;
}

/**
 * Whether a membership tier is Builder-equivalent (BUILDER or STUDENT_BUILDER).
 * Mirrors backend/app/tiers.py is_builder_equivalent. Exact match only.
 */
export function isBuilderEquivalent(tier?: string | null): boolean {
  return tier === 'BUILDER' || tier === 'STUDENT_BUILDER';
}

/**
 * Whether a subscription grants Builder access.
 *
 * A member must be on a Builder-equivalent tier (BUILDER or STUDENT_BUILDER) AND have an active subscription.
 * A past_due subscription (failed payment) does NOT grant access — the member
 * must update their payment information first. This matches the backend
 * entitlement checks in progress.py, content.py, and entitlement_service.py.
 */
export function hasBuilderAccess(
  subscription: SubscriptionAccessInfo | null | undefined
): boolean {
  if (!subscription) return false;
  return (
    isBuilderEquivalent(subscription.membership_tier) &&
    subscription.subscription_status === 'active'
  );
}

/** Whether a subscription is past due (failed payment, access suspended). */
export function isPastDue(
  subscription: SubscriptionAccessInfo | null | undefined
): boolean {
  return subscription?.subscription_status === 'past_due';
}
