/**
 * Data tests for the Video Library FAQ entries.
 */
import { FAQ_CATEGORIES } from '@/lib/data/faq';

const allQuestions = FAQ_CATEGORIES.flatMap((c) => c.questions);
const bySlug = (slug: string) => allQuestions.find((q) => q.slug === slug);

it('has a "What is the Video Library?" entry linking to the public preview', () => {
  const q = bySlug('what-is-the-video-library');
  expect(q).toBeDefined();
  expect(q?.question).toBe('What is the Video Library?');
  expect(q?.answer).toMatch(/free/i);
  expect(q?.links).toEqual(
    expect.arrayContaining([expect.objectContaining({ href: '/videos/preview' })])
  );
});

it('references the Video Library in the related entries', () => {
  for (const slug of [
    'are-live-sessions-recorded',
    'can-i-try-before-subscribing',
    'can-i-participate-without-live-events',
  ]) {
    expect(bySlug(slug)?.answer).toMatch(/Video Library/);
  }
});

it('keeps existing slugs and all slugs unique', () => {
  for (const slug of ['what-are-builder-sessions', 'is-dsb-free', 'are-live-sessions-recorded']) {
    expect(bySlug(slug)).toBeDefined();
  }
  const slugs = allQuestions.map((q) => q.slug);
  expect(new Set(slugs).size).toBe(slugs.length);
});
