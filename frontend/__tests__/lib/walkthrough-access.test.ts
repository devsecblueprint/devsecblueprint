import {
  resolveWalkthroughTiers,
  getWalkthroughTier,
  isWalkthroughLocked,
} from '@/lib/walkthrough-access';

describe('walkthrough-access', () => {
  it('treats an explicit BUILDER record as locked', () => {
    const map = resolveWalkthroughTiers({ data: { access_tiers: { a: 'BUILDER' }, default_tier: 'FREE' }, statusCode: 200 });
    expect(getWalkthroughTier('a', map)).toBe('BUILDER');
    expect(isWalkthroughLocked('a', map)).toBe(true);
  });

  it('lets an explicit FREE record override a BUILDER default', () => {
    const map = resolveWalkthroughTiers({ data: { access_tiers: { a: 'FREE' }, default_tier: 'BUILDER' }, statusCode: 200 });
    expect(getWalkthroughTier('a', map)).toBe('FREE');
    expect(isWalkthroughLocked('a', map)).toBe(false);
  });

  it('locks unlisted walkthroughs when the default is BUILDER', () => {
    const map = resolveWalkthroughTiers({ data: { access_tiers: {}, default_tier: 'BUILDER' }, statusCode: 200 });
    expect(getWalkthroughTier('new', map)).toBe('BUILDER');
    expect(isWalkthroughLocked('new', map)).toBe(true);
  });

  it('leaves unlisted walkthroughs open when the default is FREE', () => {
    const map = resolveWalkthroughTiers({ data: { access_tiers: {}, default_tier: 'FREE' }, statusCode: 200 });
    expect(getWalkthroughTier('new', map)).toBe('FREE');
    expect(isWalkthroughLocked('new', map)).toBe(false);
  });

  it('treats a response without default_tier as FREE (older backend)', () => {
    const map = resolveWalkthroughTiers({ data: { access_tiers: { a: 'BUILDER' } }, statusCode: 200 });
    expect(map.defaultTier).toBe('FREE');
    expect(isWalkthroughLocked('a', map)).toBe(true);
    expect(isWalkthroughLocked('other', map)).toBe(false);
  });

  it('treats a missing access_tiers as an empty map', () => {
    const map = resolveWalkthroughTiers({ data: { default_tier: 'BUILDER' } as never, statusCode: 200 });
    expect(map).toEqual({ tiers: {}, defaultTier: 'BUILDER' });
  });

  it.each([
    ['an error response', { error: 'unavailable', statusCode: 503 }],
    ['no data', { statusCode: 200 }],
    ['an error alongside data', { data: { access_tiers: { a: 'FREE' }, default_tier: 'FREE' }, error: 'x', statusCode: 500 }],
    ['undefined', undefined],
  ])('fails closed for %s', (_name, response) => {
    const map = resolveWalkthroughTiers(response as never);
    expect(map).toEqual({ tiers: {}, defaultTier: 'BUILDER' });
    expect(isWalkthroughLocked('a', map)).toBe(true);
  });

  it('ignores garbage tier values and falls back to the default', () => {
    const map = resolveWalkthroughTiers({
      data: { access_tiers: { a: 'PLATINUM', b: '', c: 'builder' }, default_tier: 'BUILDER' },
      statusCode: 200,
    });
    expect(getWalkthroughTier('a', map)).toBe('BUILDER');
    expect(getWalkthroughTier('b', map)).toBe('BUILDER');
    expect(getWalkthroughTier('c', map)).toBe('BUILDER');
    const freeDefault = resolveWalkthroughTiers({ data: { access_tiers: { a: 'PLATINUM' }, default_tier: 'FREE' }, statusCode: 200 });
    expect(getWalkthroughTier('a', freeDefault)).toBe('FREE');
  });

  it('fails closed for an unrecognized default_tier and ignores inherited keys', () => {
    const map = resolveWalkthroughTiers({ data: { access_tiers: {}, default_tier: 'WAT' }, statusCode: 200 });
    expect(map.defaultTier).toBe('BUILDER');
    expect(getWalkthroughTier('constructor', { tiers: {}, defaultTier: 'FREE' })).toBe('FREE');
  });
});
