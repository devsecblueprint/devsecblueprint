import { hasBuilderAccess, isPastDue } from '@/lib/entitlements';

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
