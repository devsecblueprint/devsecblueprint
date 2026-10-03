/**
 * Unit tests for lib/constants.ts — static learning-path and sample data.
 * These guard against accidental structural drift in shipped seed data.
 */
import {
  LEARNING_PATHS,
  SAMPLE_MODULES,
  SAMPLE_USER_STATS,
  SAMPLE_BADGES,
} from '@/lib/constants';

describe('LEARNING_PATHS', () => {
  it('defines the seven curriculum paths', () => {
    expect(LEARNING_PATHS).toHaveLength(7);
  });

  it('has unique ids and slugs', () => {
    expect(new Set(LEARNING_PATHS.map((p) => p.id)).size).toBe(LEARNING_PATHS.length);
    expect(new Set(LEARNING_PATHS.map((p) => p.slug)).size).toBe(LEARNING_PATHS.length);
  });

  it('every path has a non-empty title and description', () => {
    for (const p of LEARNING_PATHS) {
      expect(p.title.trim().length).toBeGreaterThan(0);
      expect(p.description.trim().length).toBeGreaterThan(0);
      expect(typeof p.moduleCount).toBe('number');
    }
  });

  it('includes the expected key slugs', () => {
    const slugs = LEARNING_PATHS.map((p) => p.slug);
    expect(slugs).toEqual(
      expect.arrayContaining(['prerequisites', 'devsecops', 'cloud-security', 'career-strategy']),
    );
  });
});

describe('SAMPLE_MODULES', () => {
  it('each module has ordered pages', () => {
    for (const m of SAMPLE_MODULES) {
      expect(m.pages.length).toBeGreaterThan(0);
      const orders = m.pages.map((pg) => pg.order);
      expect(orders).toEqual([...orders].sort((a, b) => a - b));
    }
  });
});

describe('SAMPLE_USER_STATS', () => {
  it('is a zeroed starting profile', () => {
    expect(SAMPLE_USER_STATS).toEqual({
      currentStreak: 0,
      longestStreak: 0,
      overallCompletion: 0,
      badgesEarned: 0,
    });
  });
});

describe('SAMPLE_BADGES', () => {
  it('earned badges carry an earnedDate; unearned do not', () => {
    for (const b of SAMPLE_BADGES) {
      if (b.earned) {
        expect(b.earnedDate).toBeDefined();
      } else {
        expect(b.earnedDate).toBeUndefined();
      }
    }
  });
});
