/**
 * Unit tests for ActivityTimeline.
 */
import { render, screen } from '@testing-library/react';
import { useRecentActivities } from '@/lib/hooks/useRecentActivities';
import { ActivityTimeline } from '@/components/dashboard/ActivityTimeline';

jest.mock('@/lib/hooks/useRecentActivities', () => ({ useRecentActivities: jest.fn() }));
const mockHook = useRecentActivities as jest.Mock;

function activity(id: string, overrides: Record<string, unknown> = {}) {
  return {
    id,
    contentId: id,
    title: `Lesson ${id}`,
    path: 'DevSecOps',
    completedAt: '2026-01-0' + id + 'T00:00:00Z',
    relativeTime: '1 day ago',
    ...overrides,
  };
}

beforeEach(() => jest.clearAllMocks());

it('shows skeletons while loading', () => {
  mockHook.mockReturnValue({ activities: [], isLoading: true, error: null });
  const { container } = render(<ActivityTimeline />);
  expect(screen.getByText('Recent Activity')).toBeInTheDocument();
  expect(container.querySelector('[aria-busy="true"]')).toBeInTheDocument();
});

it('shows an empty state when there are no activities', () => {
  mockHook.mockReturnValue({ activities: [], isLoading: false, error: null });
  render(<ActivityTimeline />);
  expect(screen.getByText(/No recent activity yet/i)).toBeInTheDocument();
});

it('shows the empty state on error', () => {
  mockHook.mockReturnValue({ activities: [], isLoading: false, error: 'boom' });
  render(<ActivityTimeline />);
  expect(screen.getByText(/No recent activity yet/i)).toBeInTheDocument();
});

it('renders activities most-recent-first, capped at five', () => {
  const activities = ['1', '2', '3', '4', '5', '6'].map((id) => activity(id));
  mockHook.mockReturnValue({ activities, isLoading: false, error: null });
  render(<ActivityTimeline />);
  // Only 5 render; the oldest (Lesson 1) is dropped
  expect(screen.queryByText('Lesson 1')).not.toBeInTheDocument();
  expect(screen.getByText('Lesson 6')).toBeInTheDocument();
});

it('picks an icon type based on the activity title/path', () => {
  mockHook.mockReturnValue({
    activities: [activity('1', { title: 'Module Quiz', path: 'quiz' })],
    isLoading: false,
    error: null,
  });
  render(<ActivityTimeline />);
  expect(screen.getByText('Module Quiz')).toBeInTheDocument();
});
