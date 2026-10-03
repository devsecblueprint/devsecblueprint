/**
 * Unit tests for ContinueLearningCard tri-state behavior.
 */
import { render, screen } from '@testing-library/react';
import { getAllCourses } from '@/lib/course-utils';
import { ContinueLearningCard } from '@/components/dashboard/ContinueLearningCard';

jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
}));
jest.mock('@/lib/course-utils', () => ({ getAllCourses: jest.fn() }));
const mockGetAllCourses = getAllCourses as jest.Mock;

function course(overrides: Record<string, unknown> = {}) {
  return {
    learningPath: 'DevSecOps',
    topic: 'intro',
    title: 'Intro',
    firstPageSlug: '/learn/devsecops/intro',
    lastActiveSlug: '/learn/devsecops/intro/page-2',
    completedPages: 1,
    totalPages: 4,
    percentComplete: 25,
    ...overrides,
  };
}

function renderCard(props: Partial<React.ComponentProps<typeof ContinueLearningCard>> = {}) {
  render(
    <ContinueLearningCard
      progress={{}}
      progressLoading={false}
      lastActiveSlug={null}
      lastActiveLessonLoading={false}
      {...props}
    />,
  );
}

beforeEach(() => jest.clearAllMocks());

it('shows a skeleton while progress is loading', () => {
  mockGetAllCourses.mockReturnValue([]);
  const { container } = render(
    <ContinueLearningCard progress={{}} progressLoading lastActiveSlug={null} lastActiveLessonLoading={false} />,
  );
  expect(screen.getByText('Continue Where You Left Off')).toBeInTheDocument();
  expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
});

it('shows the onboarding state for a new user with no progress', () => {
  mockGetAllCourses.mockReturnValue([course({ percentComplete: 0 })]);
  renderCard();
  expect(screen.getByText('Start Your Learning Journey')).toBeInTheDocument();
  expect(screen.getByText(/Welcome to The DevSec Blueprint/i)).toBeInTheDocument();
});

it('shows the active-learning state with a resume course', () => {
  mockGetAllCourses.mockReturnValue([course({ percentComplete: 25 })]);
  renderCard({ lastActiveSlug: '/learn/devsecops/intro/page-2' });
  expect(screen.getByText('Continue Where You Left Off')).toBeInTheDocument();
  expect(screen.getByText('Intro')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /continue learning/i })).toBeInTheDocument();
});

it('shows a loading button when the last active lesson is still loading', () => {
  mockGetAllCourses.mockReturnValue([course({ percentComplete: 25 })]);
  renderCard({ lastActiveLessonLoading: true });
  expect(screen.getByRole('button', { name: /loading/i })).toBeDisabled();
});

it('shows the completion state when all courses are complete', () => {
  mockGetAllCourses.mockReturnValue([course({ percentComplete: 100, completedPages: 4 })]);
  renderCard();
  expect(screen.getByText('Congratulations!')).toBeInTheDocument();
  expect(screen.getByText(/Completed All Available Courses/i)).toBeInTheDocument();
});

it('filters out walkthroughs from the course set', () => {
  mockGetAllCourses.mockReturnValue([
    course({ percentComplete: 100, completedPages: 4 }),
    course({ learningPath: 'Walkthroughs', topic: 'wt', percentComplete: 0 }),
  ]);
  renderCard();
  // Walkthrough at 0% would otherwise make this "active"; filtering it out => completion
  expect(screen.getByText('Congratulations!')).toBeInTheDocument();
});
