import { hasBuilderAccess, isBuilderEquivalent, isPastDue } from '@/lib/entitlements';

describe('hasBuilderAccess', () => {
  it('grants access for BUILDER tier with active subscription', () => {
    expect(
      hasBuilderAccess({ membership_tier: 'BUILDER', subscription_status: 'active' })
    ).toBe(true);
  });

  it('denies access when tier is not BUILDER', () => {
    expect(
      hasBuilderAccess({ membership_tier: 'FREE', subscription_status: 'active' })
    ).toBe(false);
  });

  it('denies access when subscription is not active', () => {
    expect(
      hasBuilderAccess({ membership_tier: 'BUILDER', subscription_status: 'past_due' })
    ).toBe(false);
    expect(
      hasBuilderAccess({ membership_tier: 'BUILDER', subscription_status: 'canceled' })
    ).toBe(false);
  });

  it('denies access for null/undefined subscription', () => {
    expect(hasBuilderAccess(null)).toBe(false);
    expect(hasBuilderAccess(undefined)).toBe(false);
  });

  it('denies access when fields are missing', () => {
    expect(hasBuilderAccess({})).toBe(false);
    expect(hasBuilderAccess({ membership_tier: 'BUILDER' })).toBe(false);
    expect(hasBuilderAccess({ subscription_status: 'active' })).toBe(false);
  });
});

describe('isPastDue', () => {
  it('returns true only for past_due status', () => {
    expect(isPastDue({ subscription_status: 'past_due' })).toBe(true);
  });

  it('returns false for other statuses and empty input', () => {
    expect(isPastDue({ subscription_status: 'active' })).toBe(false);
    expect(isPastDue({})).toBe(false);
    expect(isPastDue(null)).toBe(false);
    expect(isPastDue(undefined)).toBe(false);
  });
});

describe('isBuilderEquivalent', () => {
  it('is true only for exactly BUILDER and STUDENT_BUILDER', () => {
    expect(isBuilderEquivalent('BUILDER')).toBe(true);
    expect(isBuilderEquivalent('STUDENT_BUILDER')).toBe(true);
  });

  it('is false for null, undefined, empty, lowercase, and other tiers', () => {
    for (const t of [null, undefined, '', 'builder', 'student_builder', 'FREE', 'EXPLORER']) {
      expect(isBuilderEquivalent(t)).toBe(false);
    }
  });
});

describe('hasBuilderAccess for STUDENT_BUILDER', () => {
  it('grants access when active', () => {
    expect(
      hasBuilderAccess({ membership_tier: 'STUDENT_BUILDER', subscription_status: 'active' })
    ).toBe(true);
  });

  it('denies access when past_due', () => {
    expect(
      hasBuilderAccess({ membership_tier: 'STUDENT_BUILDER', subscription_status: 'past_due' })
    ).toBe(false);
  });

  it('denies access for FREE, null and undefined tiers', () => {
    expect(hasBuilderAccess({ membership_tier: 'FREE', subscription_status: 'active' })).toBe(false);
    expect(hasBuilderAccess({ membership_tier: null, subscription_status: 'active' })).toBe(false);
    expect(hasBuilderAccess({ subscription_status: 'active' })).toBe(false);
  });
});
