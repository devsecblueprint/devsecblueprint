import { getAllCourses, getLearningPathTitle } from '@/lib/course-utils';

describe('getAllCourses', () => {
  it('returns courses with sane progress defaults when no progress given', () => {
    const courses = getAllCourses();
    expect(courses.length).toBeGreaterThan(0);
    courses.forEach((c) => {
      expect(c.totalPages).toBeGreaterThanOrEqual(0);
      expect(c.completedPages).toBe(0);
      expect(c.percentComplete).toBe(0);
      expect(typeof c.firstPageSlug).toBe('string');
      expect(c.lastActiveSlug).toBeTruthy();
    });
  });

  it('computes completion percentage from the progress map', () => {
    const courses = getAllCourses();
    const target = courses.find((c) => c.totalPages > 0);
    expect(target).toBeDefined();

    // Mark the first page of the target module complete via its page id.
    const firstModule = target!.modules[0] as any;
    const firstPage = firstModule.pages[0];
    const progress = { [firstPage.id]: true };

    const updated = getAllCourses(progress).find((c) => c.title === target!.title)!;
    expect(updated.completedPages).toBeGreaterThanOrEqual(1);
    expect(updated.percentComplete).toBeGreaterThan(0);
  });

  it('ignores an invalid lastActiveSlug', () => {
    const courses = getAllCourses({}, '/learn/not-a-real-slug');
    // Falls back to firstIncomplete/firstPage, never the bogus slug.
    courses.forEach((c) => {
      expect(c.lastActiveSlug).not.toBe('/learn/not-a-real-slug');
    });
  });

  it('honors a valid lastActiveSlug', () => {
    const courses = getAllCourses();
    const someSlug = (courses[0].modules[0] as any).pages[0].slug;
    const result = getAllCourses({}, someSlug);
    const match = result.find((c) =>
      (c.modules[0] as any).pages.some((p: any) => p.slug === someSlug)
    );
    expect(match!.lastActiveSlug).toBe(someSlug);
  });
});

describe('getLearningPathTitle', () => {
  it('maps known slugs to display titles', () => {
    expect(getLearningPathTitle('devsecops')).toBe('DevSecOps');
    expect(getLearningPathTitle('know_before_you_go')).toBe('Know Before You Go');
    expect(getLearningPathTitle('cloud_security')).toBe('Cloud Security');
  });

  it('formats unknown underscored slugs into Title Case', () => {
    expect(getLearningPathTitle('some_new_path')).toBe('Some New Path');
  });

  it('passes through already-formatted known values', () => {
    expect(getLearningPathTitle('Getting Started')).toBe('Getting Started');
  });
});
