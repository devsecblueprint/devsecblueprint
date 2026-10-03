/**
 * Unit tests for AllCoursesClient.
 */
import { render, screen } from '@testing-library/react';
import { useAllProgress } from '@/lib/hooks/useAllProgress';
import { getAllCourses, getLearningPathTitle } from '@/lib/course-utils';
import { AllCoursesClient } from '@/components/AllCoursesClient';

jest.mock('@/lib/hooks/useAllProgress', () => ({ useAllProgress: jest.fn() }));
jest.mock('@/lib/course-utils', () => ({
  getAllCourses: jest.fn(),
  getLearningPathTitle: jest.fn((p: string) => `Path: ${p}`),
}));

const mockUseAllProgress = useAllProgress as jest.Mock;
const mockGetAllCourses = getAllCourses as jest.Mock;

function course(overrides: Record<string, unknown> = {}) {
  return {
    learningPath: 'DevSecOps',
    topic: 'intro',
    title: 'Intro to DevSecOps',
    firstPageSlug: '/learn/devsecops/intro',
    completedPages: 2,
    totalPages: 4,
    percentComplete: 50,
    ...overrides,
  };
}

beforeEach(() => jest.clearAllMocks());

it('shows a spinner while progress is loading', () => {
  mockUseAllProgress.mockReturnValue({ progress: {}, isLoading: true });
  mockGetAllCourses.mockReturnValue([]);
  const { container } = render(<AllCoursesClient />);
  expect(container.querySelector('.animate-spin')).toBeInTheDocument();
});

it('shows an empty message when there are no courses', () => {
  mockUseAllProgress.mockReturnValue({ progress: {}, isLoading: false });
  mockGetAllCourses.mockReturnValue([]);
  render(<AllCoursesClient />);
  expect(screen.getByText(/No courses available yet/i)).toBeInTheDocument();
});

it('renders grouped courses with the learning path title', () => {
  mockUseAllProgress.mockReturnValue({ progress: {}, isLoading: false });
  mockGetAllCourses.mockReturnValue([course()]);
  render(<AllCoursesClient />);
  expect(screen.getByText('Path: DevSecOps')).toBeInTheDocument();
  expect(screen.getByText('Intro to DevSecOps')).toBeInTheDocument();
  expect(screen.getByText('2 of 4 lessons')).toBeInTheDocument();
});

it('filters out walkthroughs', () => {
  mockUseAllProgress.mockReturnValue({ progress: {}, isLoading: false });
  mockGetAllCourses.mockReturnValue([
    course({ title: 'Keep Me' }),
    course({ learningPath: 'Walkthroughs', title: 'Drop Me', topic: 'wt' }),
  ]);
  render(<AllCoursesClient />);
  expect(screen.getByText('Keep Me')).toBeInTheDocument();
  expect(screen.queryByText('Drop Me')).not.toBeInTheDocument();
});

it('shows the right action label per completion state', () => {
  mockUseAllProgress.mockReturnValue({ progress: {}, isLoading: false });
  mockGetAllCourses.mockReturnValue([
    course({ title: 'Not Started', topic: 'a', percentComplete: 0 }),
    course({ title: 'In Progress', topic: 'b', percentComplete: 50 }),
    course({ title: 'Done', topic: 'c', percentComplete: 100 }),
  ]);
  render(<AllCoursesClient />);
  expect(screen.getByText('Start Course')).toBeInTheDocument();
  expect(screen.getByText('Continue Learning')).toBeInTheDocument();
  expect(screen.getByText('Review Course')).toBeInTheDocument();
});

it('renders overall stats (total, completed, lessons completed)', () => {
  mockUseAllProgress.mockReturnValue({ progress: {}, isLoading: false });
  mockGetAllCourses.mockReturnValue([
    course({ title: 'A', topic: 'a', percentComplete: 100, completedPages: 4 }),
    course({ title: 'B', topic: 'b', percentComplete: 50, completedPages: 2 }),
  ]);
  render(<AllCoursesClient />);
  expect(screen.getByText('Total Courses')).toBeInTheDocument();
  expect(screen.getByText('Completed Courses')).toBeInTheDocument();
  expect(screen.getByText('Total Lessons Completed')).toBeInTheDocument();
  // 4 + 2 = 6 lessons completed
  expect(screen.getByText('6')).toBeInTheDocument();
});
