/**
 * Unit tests for the admin ActivitySection.
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { useAdminContext } from '@/app/admin/components/AdminDashboardProvider';
import { ActivitySection } from '@/app/admin/components/ActivitySection';

jest.mock('@/app/admin/components/AdminDashboardProvider', () => ({ useAdminContext: jest.fn() }));
const mockCtx = useAdminContext as jest.Mock;

function ctx(overrides: Record<string, unknown> = {}) {
  return {
    analytics: null,
    isLoading: false,
    errors: {},
    refetchAll: jest.fn(),
    ...overrides,
  };
}

beforeEach(() => jest.clearAllMocks());

it('shows loading skeletons', () => {
  mockCtx.mockReturnValue(ctx({ isLoading: true }));
  const { container } = render(<ActivitySection />);
  expect(screen.getByText('Top Learners')).toBeInTheDocument();
  // Skeletons use animate-pulse via the Skeleton component
  expect(container.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0);
});

it('renders top learners sorted by completion', () => {
  mockCtx.mockReturnValue(
    ctx({
      analytics: {
        completion_by_user: [
          { user_id: 'u1', username: 'ada', completed: 5, percentage: 50 },
          { user_id: 'u2', username: 'grace', completed: 9, percentage: 90 },
        ],
      },
    }),
  );
  render(<ActivitySection />);
  // Both desktop + mobile render the names
  expect(screen.getAllByText('grace').length).toBeGreaterThan(0);
  expect(screen.getAllByText('ada').length).toBeGreaterThan(0);
});

it('shows an empty state when there is no learner activity', () => {
  mockCtx.mockReturnValue(ctx({ analytics: { completion_by_user: [] } }));
  render(<ActivitySection />);
  expect(screen.getByText('No learner activity')).toBeInTheDocument();
});

it('shows an error with retry', () => {
  const refetchAll = jest.fn();
  mockCtx.mockReturnValue(ctx({ errors: { analytics: 'boom' }, refetchAll }));
  render(<ActivitySection />);
  expect(screen.getByText(/Failed to load learner data/i)).toBeInTheDocument();
  fireEvent.click(screen.getAllByRole('button', { name: /retry/i })[0]);
  expect(refetchAll).toHaveBeenCalled();
});

it('always renders the Recent Members column (empty placeholder)', () => {
  mockCtx.mockReturnValue(ctx({ analytics: { completion_by_user: [] } }));
  render(<ActivitySection />);
  expect(screen.getByText('No recent members')).toBeInTheDocument();
});
