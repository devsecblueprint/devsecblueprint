/**
 * ActivityTimeline Component Tests
 * Task 4.2: Create ActivityTimeline component
 *
 * Validates:
 * - Loading state shows 5 skeleton items (Requirement 5.9)
 * - Empty state shows encouragement message (Requirement 5.4)
 * - Displays max 5 activities sorted by most recent (Requirements 5.2, 5.3)
 * - Activity type icons render correctly (Requirement 5.2)
 * - "View all activity" link appears when > 5 activities (Requirement 5.5)
 * - Error state shows empty state without blocking siblings (Requirement 5.11)
 * - Uses h2 heading "Recent Activity" (Requirement 5.1)
 */

import { render, screen } from './test-utils';
import { ActivityTimeline } from '@/components/dashboard/ActivityTimeline';

// Mock the useRecentActivities hook
const mockUseRecentActivities = jest.fn();
jest.mock('@/lib/hooks/useRecentActivities', () => ({
  useRecentActivities: () => mockUseRecentActivities(),
}));

function makeActivity(overrides: Partial<{
  id: string;
  contentId: string;
  title: string;
  path: string;
  completedAt: string;
  relativeTime: string;
}> = {}) {
  return {
    id: overrides.id ?? '1',
    contentId: overrides.contentId ?? 'module/lesson',
    title: overrides.title ?? 'Test Lesson',
    path: overrides.path ?? 'Test Module',
    completedAt: overrides.completedAt ?? '2024-01-15T10:00:00Z',
    relativeTime: overrides.relativeTime ?? '2 hours ago',
  };
}

describe('ActivityTimeline', () => {
  beforeEach(() => {
    mockUseRecentActivities.mockReset();
  });

  describe('Section heading', () => {
    it('renders h2 heading "Recent Activity"', () => {
      mockUseRecentActivities.mockReturnValue({
        activities: [],
        isLoading: false,
        error: null,
      });

      render(<ActivityTimeline />);
      const heading = screen.getByRole('heading', { level: 2, name: /recent activity/i });
      expect(heading).toBeInTheDocument();
    });
  });

  describe('Loading state', () => {
    it('shows 5 skeleton items with animate-pulse while loading', () => {
      mockUseRecentActivities.mockReturnValue({
        activities: [],
        isLoading: true,
        error: null,
      });

      const { container } = render(<ActivityTimeline />);
      // SkeletonActivityCard renders elements with animate-pulse
      const skeletons = container.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBeGreaterThanOrEqual(5);
    });

    it('sets aria-busy true while loading', () => {
      mockUseRecentActivities.mockReturnValue({
        activities: [],
        isLoading: true,
        error: null,
      });

      const { container } = render(<ActivityTimeline />);
      const liveRegion = container.querySelector('[aria-busy="true"]');
      expect(liveRegion).toBeInTheDocument();
    });
  });

  describe('Empty state', () => {
    it('shows encouragement message when no activities', () => {
      mockUseRecentActivities.mockReturnValue({
        activities: [],
        isLoading: false,
        error: null,
      });

      render(<ActivityTimeline />);
      expect(screen.getByText(/no recent activity yet/i)).toBeInTheDocument();
      expect(screen.getByText(/start a lesson or quiz/i)).toBeInTheDocument();
    });

    it('shows "Browse Courses" link in empty state', () => {
      mockUseRecentActivities.mockReturnValue({
        activities: [],
        isLoading: false,
        error: null,
      });

      render(<ActivityTimeline />);
      const link = screen.getByRole('link', { name: /browse courses/i });
      expect(link).toHaveAttribute('href', '/courses');
    });
  });

  describe('Error state', () => {
    it('shows empty state on error without crashing', () => {
      mockUseRecentActivities.mockReturnValue({
        activities: [],
        isLoading: false,
        error: 'Network error',
      });

      render(<ActivityTimeline />);
      expect(screen.getByText(/no recent activity yet/i)).toBeInTheDocument();
    });
  });

  describe('Activity rendering', () => {
    it('displays activities with title and relative timestamp', () => {
      mockUseRecentActivities.mockReturnValue({
        activities: [
          makeActivity({ id: '1', title: 'Introduction to SAST', path: 'DevSecOps', relativeTime: '3 hours ago' }),
        ],
        isLoading: false,
        error: null,
      });

      render(<ActivityTimeline />);
      expect(screen.getByText('Introduction to SAST')).toBeInTheDocument();
      expect(screen.getByText('DevSecOps')).toBeInTheDocument();
      expect(screen.getByText('3 hours ago')).toBeInTheDocument();
    });

    it('renders max 5 activities even if more are returned', () => {
      const activities = Array.from({ length: 8 }, (_, i) =>
        makeActivity({
          id: `${i}`,
          title: `Activity ${i}`,
          completedAt: `2024-01-${String(15 - i).padStart(2, '0')}T10:00:00Z`,
          relativeTime: `${i} hours ago`,
        })
      );

      mockUseRecentActivities.mockReturnValue({
        activities,
        isLoading: false,
        error: null,
      });

      render(<ActivityTimeline />);
      // Should only render 5 activity titles
      const headings = screen.getAllByRole('heading', { level: 3 });
      expect(headings).toHaveLength(5);
    });

    it('orders activities by most recent first', () => {
      const activities = [
        makeActivity({ id: '1', title: 'Older', completedAt: '2024-01-10T10:00:00Z', relativeTime: '5 days ago' }),
        makeActivity({ id: '2', title: 'Newest', completedAt: '2024-01-15T10:00:00Z', relativeTime: '1 hour ago' }),
        makeActivity({ id: '3', title: 'Middle', completedAt: '2024-01-12T10:00:00Z', relativeTime: '3 days ago' }),
      ];

      mockUseRecentActivities.mockReturnValue({
        activities,
        isLoading: false,
        error: null,
      });

      render(<ActivityTimeline />);
      const headings = screen.getAllByRole('heading', { level: 3 });
      expect(headings[0]).toHaveTextContent('Newest');
      expect(headings[1]).toHaveTextContent('Middle');
      expect(headings[2]).toHaveTextContent('Older');
    });
  });

  describe('Activity type icons', () => {
    it('shows checkmark icon for quiz activities', () => {
      mockUseRecentActivities.mockReturnValue({
        activities: [makeActivity({ id: '1', title: 'Quiz: Security Basics', path: 'Quizzes' })],
        isLoading: false,
        error: null,
      });

      const { container } = render(<ActivityTimeline />);
      // Quiz icon uses green styling
      const greenIcon = container.querySelector('.bg-green-100');
      expect(greenIcon).toBeInTheDocument();
    });

    it('shows code icon for walkthrough activities', () => {
      mockUseRecentActivities.mockReturnValue({
        activities: [makeActivity({ id: '1', title: 'Walkthrough: Deploy Pipeline', path: 'Walkthroughs' })],
        isLoading: false,
        error: null,
      });

      const { container } = render(<ActivityTimeline />);
      // Walkthrough icon uses amber styling
      const amberIcon = container.querySelector('.bg-amber-100');
      expect(amberIcon).toBeInTheDocument();
    });

    it('shows trophy icon for badge activities', () => {
      mockUseRecentActivities.mockReturnValue({
        activities: [makeActivity({ id: '1', title: 'Badge Earned: First Steps', path: 'Badges' })],
        isLoading: false,
        error: null,
      });

      const { container } = render(<ActivityTimeline />);
      // Badge icon uses purple styling
      const purpleIcon = container.querySelector('.bg-purple-100');
      expect(purpleIcon).toBeInTheDocument();
    });

    it('shows book icon for lesson activities', () => {
      mockUseRecentActivities.mockReturnValue({
        activities: [makeActivity({ id: '1', title: 'Introduction to DevOps', path: 'Lessons' })],
        isLoading: false,
        error: null,
      });

      const { container } = render(<ActivityTimeline />);
      // Lesson icon uses green styling (book)
      const greenIcon = container.querySelector('.bg-green-100');
      expect(greenIcon).toBeInTheDocument();
    });
  });

  describe('View all activity link', () => {
    it('shows "View all activity" link when > 5 activities', () => {
      const activities = Array.from({ length: 7 }, (_, i) =>
        makeActivity({
          id: `${i}`,
          title: `Activity ${i}`,
          completedAt: `2024-01-${String(15 - i).padStart(2, '0')}T10:00:00Z`,
        })
      );

      mockUseRecentActivities.mockReturnValue({
        activities,
        isLoading: false,
        error: null,
      });

      render(<ActivityTimeline />);
      const viewAllLink = screen.getByRole('link', { name: /view all activity/i });
      expect(viewAllLink).toBeInTheDocument();
    });

    it('does not show "View all activity" link when <= 5 activities', () => {
      const activities = [
        makeActivity({ id: '1', title: 'Activity 1' }),
        makeActivity({ id: '2', title: 'Activity 2' }),
      ];

      mockUseRecentActivities.mockReturnValue({
        activities,
        isLoading: false,
        error: null,
      });

      render(<ActivityTimeline />);
      expect(screen.queryByRole('link', { name: /view all activity/i })).not.toBeInTheDocument();
    });
  });
});
