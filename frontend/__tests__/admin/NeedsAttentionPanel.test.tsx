/**
 * Unit tests for NeedsAttentionPanel.
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { useAdminContext } from '@/app/admin/components/AdminDashboardProvider';
import { NeedsAttentionPanel } from '@/app/admin/components/NeedsAttentionPanel';

jest.mock('@/app/admin/components/AdminDashboardProvider', () => ({ useAdminContext: jest.fn() }));
const mockCtx = useAdminContext as jest.Mock;

function ctx(overrides: Record<string, unknown> = {}) {
  return {
    attentionCounts: { pendingCapstones: 0, pendingTestimonials: 0, moduleHealthIssues: 0, registryIssues: 0 },
    isLoading: false,
    errors: { submissions: null, moduleHealth: null, registryStatus: null },
    refetchAll: jest.fn(),
    ...overrides,
  };
}

beforeEach(() => jest.clearAllMocks());

it('shows a loading skeleton', () => {
  mockCtx.mockReturnValue(ctx({ isLoading: true }));
  render(<NeedsAttentionPanel />);
  expect(screen.getByLabelText('Loading attention items')).toBeInTheDocument();
});

it('shows the all-clear state when every count is zero', () => {
  mockCtx.mockReturnValue(ctx());
  render(<NeedsAttentionPanel />);
  expect(screen.getByText('No items require attention')).toBeInTheDocument();
});

it('lists attention items with counts', () => {
  mockCtx.mockReturnValue(
    ctx({ attentionCounts: { pendingCapstones: 2, pendingTestimonials: 1, moduleHealthIssues: 0, registryIssues: 0 } }),
  );
  render(<NeedsAttentionPanel />);
  expect(screen.getByText('Pending Capstone Submissions')).toBeInTheDocument();
  expect(screen.getByText('2')).toBeInTheDocument();
});

it('scrolls to the target section on click', () => {
  const scrollIntoView = jest.fn();
  const target = document.createElement('div');
  target.id = 'reviews';
  target.scrollIntoView = scrollIntoView;
  document.body.appendChild(target);

  mockCtx.mockReturnValue(
    ctx({ attentionCounts: { pendingCapstones: 2, pendingTestimonials: 0, moduleHealthIssues: 0, registryIssues: 0 } }),
  );
  render(<NeedsAttentionPanel />);
  fireEvent.click(screen.getByRole('button', { name: /Pending Capstone Submissions/i }));
  expect(scrollIntoView).toHaveBeenCalled();
  document.body.removeChild(target);
});

it('shows an error state with retry', () => {
  const refetchAll = jest.fn();
  mockCtx.mockReturnValue(
    ctx({ errors: { submissions: 'boom', moduleHealth: null, registryStatus: null }, refetchAll }),
  );
  render(<NeedsAttentionPanel />);
  expect(screen.getByText(/Failed to load attention data/i)).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /retry/i }));
  expect(refetchAll).toHaveBeenCalled();
});
