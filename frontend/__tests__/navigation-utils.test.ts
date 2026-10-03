import { getAllPagesInOrder, getAdjacentPages } from '@/lib/navigation-utils';

describe('getAllPagesInOrder', () => {
  it('returns a non-empty, flat list of pages', () => {
    const pages = getAllPagesInOrder();
    expect(Array.isArray(pages)).toBe(true);
    expect(pages.length).toBeGreaterThan(0);
    pages.forEach((p) => {
      expect(typeof p.slug).toBe('string');
      expect(typeof p.title).toBe('string');
    });
  });

  it('is stable across calls (deterministic ordering)', () => {
    const a = getAllPagesInOrder().map((p) => p.slug);
    const b = getAllPagesInOrder().map((p) => p.slug);
    expect(a).toEqual(b);
  });
});

describe('getAdjacentPages', () => {
  it('returns empty object for an unknown slug', () => {
    expect(getAdjacentPages('/learn/does-not-exist')).toEqual({});
  });

  it('has no previous page for the first page', () => {
    const first = getAllPagesInOrder()[0];
    const { previousPage, nextPage } = getAdjacentPages(first.slug);
    expect(previousPage).toBeUndefined();
    expect(nextPage).toBeDefined();
    expect(nextPage!.slug).toBe(getAllPagesInOrder()[1].slug);
  });

  it('has no next page for the last page', () => {
    const pages = getAllPagesInOrder();
    const last = pages[pages.length - 1];
    const { previousPage, nextPage } = getAdjacentPages(last.slug);
    expect(nextPage).toBeUndefined();
    expect(previousPage).toBeDefined();
    expect(previousPage!.slug).toBe(pages[pages.length - 2].slug);
  });

  it('returns correct neighbors for a middle page', () => {
    const pages = getAllPagesInOrder();
    const midIndex = Math.floor(pages.length / 2);
    const mid = pages[midIndex];
    const { previousPage, nextPage } = getAdjacentPages(mid.slug);
    expect(previousPage!.slug).toBe(pages[midIndex - 1].slug);
    expect(nextPage!.slug).toBe(pages[midIndex + 1].slug);
  });
});
