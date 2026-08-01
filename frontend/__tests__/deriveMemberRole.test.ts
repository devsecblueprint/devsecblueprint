import { deriveMemberRole } from '@/components/dashboard/utils';
import type { ContributorRole } from '@/lib/types';

describe('deriveMemberRole', () => {
  const contributorRole: ContributorRole = {
    role: 'contributor',
    assigned_by: 'admin-user',
    assigned_at: '2024-01-01T00:00:00Z',
    note: 'Active contributor',
  };

  it('returns "admin" when isAdmin is true', () => {
    expect(deriveMemberRole(true, null)).toBe('admin');
  });

  it('returns "admin" when isAdmin is true even with contributorRole', () => {
    expect(deriveMemberRole(true, contributorRole)).toBe('admin');
  });

  it('returns "contributor" when contributorRole is not null and isAdmin is false', () => {
    expect(deriveMemberRole(false, contributorRole)).toBe('contributor');
  });

  it('returns "free" when isAdmin is false and contributorRole is null', () => {
    expect(deriveMemberRole(false, null)).toBe('free');
  });

  it('never throws for any valid input combination', () => {
    const cases: [boolean, ContributorRole | null][] = [
      [true, null],
      [true, contributorRole],
      [false, null],
      [false, contributorRole],
    ];

    for (const [isAdmin, role] of cases) {
      expect(() => deriveMemberRole(isAdmin, role)).not.toThrow();
    }
  });

  it('always returns a valid MemberRole value', () => {
    const validRoles = ['free', 'builder', 'scholar', 'contributor', 'admin'];
    const cases: [boolean, ContributorRole | null][] = [
      [true, null],
      [true, contributorRole],
      [false, null],
      [false, contributorRole],
    ];

    for (const [isAdmin, role] of cases) {
      const result = deriveMemberRole(isAdmin, role);
      expect(validRoles).toContain(result);
    }
  });
});
