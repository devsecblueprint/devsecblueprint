/**
 * StudentDiscountCard — savings-heading rounding property test (Task 18.2).
 *
 * Feature: student-builder-membership, Property 15: Student-vs-Builder savings
 * heading rounding.
 *
 * Validates: Requirements 8.8, 8.9 ; Property 15
 *
 * The component exports `computeStudentSavingsPercent(builderPrice, studentPrice)`.
 * For usable inputs (b > 0, 0 <= s <= b) it must return
 *   round(((b - s) / b) * 100 / 5) * 5
 * and for unusable inputs (b <= 0, s < 0, s > b, undefined) it must return null —
 * which is what lets the card omit the computed savings percent when the two
 * tiers don't share a common billing interval (Requirement 8.9).
 */
import fc from 'fast-check';
import { computeStudentSavingsPercent } from '@/app/pricing/StudentDiscountCard';

describe('computeStudentSavingsPercent (Property 15)', () => {
  it('returns round(((b-s)/b)*100/5)*5 for all usable (b, s) pairs', () => {
    fc.assert(
      fc.property(
        // b is a positive integer (cents); s is in [0, b].
        fc.integer({ min: 1, max: 1_000_000 }),
        fc.double({ min: 0, max: 1, noNaN: true }),
        (b, fraction) => {
          const s = Math.round(b * fraction); // 0 <= s <= b
          const expected = Math.round(((b - s) / b) * 100 / 5) * 5;
          expect(computeStudentSavingsPercent(b, s)).toBe(expected);
        }
      ),
      { numRuns: 200 }
    );
  });

  it('returns null for unusable inputs (b <= 0, s < 0, s > b, undefined)', () => {
    fc.assert(
      fc.property(
        fc.oneof(
          // b <= 0
          fc.record({
            b: fc.integer({ min: -1_000_000, max: 0 }),
            s: fc.integer({ min: 0, max: 1_000_000 }),
          }),
          // s < 0
          fc.record({
            b: fc.integer({ min: 1, max: 1_000_000 }),
            s: fc.integer({ min: -1_000_000, max: -1 }),
          }),
          // s > b
          fc
            .integer({ min: 1, max: 1_000_000 })
            .chain((b) =>
              fc.record({
                b: fc.constant(b),
                s: fc.integer({ min: b + 1, max: b + 1_000_001 }),
              })
            )
        ),
        ({ b, s }) => {
          expect(computeStudentSavingsPercent(b, s)).toBeNull();
        }
      ),
      { numRuns: 200 }
    );
  });

  it('returns null when either price is undefined (no shared interval)', () => {
    expect(computeStudentSavingsPercent(undefined, 1000)).toBeNull();
    expect(computeStudentSavingsPercent(2000, undefined)).toBeNull();
    expect(computeStudentSavingsPercent(undefined, undefined)).toBeNull();
  });

  it('rounds to the nearest 5 percent on concrete examples', () => {
    // 2000 -> 1500 is 25% exactly.
    expect(computeStudentSavingsPercent(2000, 1500)).toBe(25);
    // 2000 -> 1560 is 22% -> rounds to 20.
    expect(computeStudentSavingsPercent(2000, 1560)).toBe(20);
    // 2000 -> 1540 is 23% -> rounds to 25.
    expect(computeStudentSavingsPercent(2000, 1540)).toBe(25);
    // equal prices -> 0% savings.
    expect(computeStudentSavingsPercent(2000, 2000)).toBe(0);
  });
});
