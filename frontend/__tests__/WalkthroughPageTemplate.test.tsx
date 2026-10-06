/**
 * Unit tests for WalkthroughPageTemplate.
 */
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { useAuth } from '@/lib/hooks/useAuth';
import { apiClient } from '@/lib/api';
import { WalkthroughPageTemplate } from '@/components/WalkthroughPageTemplate';

jest.mock('next/navigation', () => ({ useRouter: () => ({ push: jest.fn() }) }));
jest.mock('@/lib/hooks/useAuth', () => ({ useAuth: jest.fn() }));
jest.mock('@/lib/api', () => ({
  apiClient: {
    get: jest.fn(),
    getUserProfile: jest.fn(),
    getWalkthroughAccessTiers: jest.fn(),
    getWalkthroughProgress: jest.fn(),
    updateWalkthroughProgress: jest.fn(),
  },
}));
jest.mock('@/lib/events', () => ({ triggerBadgeCheck: jest.fn() }));
jest.mock('@/components/AuthGuard', () => ({ AuthGuard: ({ children }: { children: React.ReactNode }) => <>{children}</> }));
jest.mock('@/components/ErrorBoundary', () => ({ ErrorBoundary: ({ children }: { children: React.ReactNode }) => <>{children}</> }));
jest.mock('@/components/layout/NavbarWithAuth', () => ({ NavbarWithAuth: () => <nav /> }));
jest.mock('@/components/WalkthroughDetail', () => ({
  WalkthroughDetail: ({ walkthrough, onMarkComplete }: { walkthrough: { title: string }; onMarkComplete: () => void }) => (
    <div>
      <span data-testid="detail">{walkthrough.title}</span>
      <button onClick={onMarkComplete}>mark-complete</button>
    </div>
  ),
}));

const mockUseAuth = useAuth as jest.Mock;
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

const walkthrough = {
  id: 'wt-1',
  title: 'AWS Lab',
  description: 'desc',
  difficulty: 'Beginner',
  estimatedTime: 30,
  topics: ['aws'],
  authors: [],
} as never;

beforeEach(() => {
  jest.clearAllMocks();
  mockApi.getUserProfile.mockResolvedValue({ data: { contributor_role: null } as never, statusCode: 200 });
  mockApi.getWalkthroughProgress.mockResolvedValue({
    data: { progress: { status: 'in_progress', started_at: '2026-01-01' } },
    statusCode: 200,
  });
  mockApi.updateWalkthroughProgress.mockResolvedValue({ data: { message: 'ok' }, statusCode: 200 });
});

it('renders the full detail for an admin (unlocked access)', async () => {
  mockUseAuth.mockReturnValue({ isAuthenticated: true, isAdmin: true });
  mockApi.get.mockResolvedValue({ data: { membership_tier: 'FREE' } as never, statusCode: 200 });
  mockApi.getWalkthroughAccessTiers.mockResolvedValue({ data: { access_tiers: { 'wt-1': 'BUILDER' } }, statusCode: 200 });

  render(<WalkthroughPageTemplate walkthrough={walkthrough} readme="# r" />);
  expect(await screen.findByTestId('detail')).toHaveTextContent('AWS Lab');
});

it('shows the upgrade prompt for a free user on a locked walkthrough', async () => {
  mockUseAuth.mockReturnValue({ isAuthenticated: true, isAdmin: false });
  mockApi.get.mockResolvedValue({ data: { membership_tier: 'FREE', subscription_status: 'inactive' } as never, statusCode: 200 });
  mockApi.getWalkthroughAccessTiers.mockResolvedValue({ data: { access_tiers: { 'wt-1': 'BUILDER' } }, statusCode: 200 });

  render(<WalkthroughPageTemplate walkthrough={walkthrough} readme="# r" />);
  expect(await screen.findByText('Upgrade to continue')).toBeInTheDocument();
  expect(screen.queryByTestId('detail')).not.toBeInTheDocument();
});

it('grants access to active Builder members on a locked walkthrough', async () => {
  mockUseAuth.mockReturnValue({ isAuthenticated: true, isAdmin: false });
  mockApi.get.mockResolvedValue({
    data: { membership_tier: 'BUILDER', subscription_status: 'active' } as never,
    statusCode: 200,
  });
  mockApi.getWalkthroughAccessTiers.mockResolvedValue({ data: { access_tiers: { 'wt-1': 'BUILDER' } }, statusCode: 200 });

  render(<WalkthroughPageTemplate walkthrough={walkthrough} readme="# r" />);
  expect(await screen.findByTestId('detail')).toBeInTheDocument();
});

it.each([
  undefined,
  { membership_tier: 'FREE', subscription_status: 'inactive' },
  { membership_tier: 'BUILDER', subscription_status: 'past_due' },
])('grants a contributor full access without an active subscription (%p)', async (subscription) => {
  mockUseAuth.mockReturnValue({ isAuthenticated: true, isAdmin: false });
  mockApi.get.mockResolvedValue({ data: subscription as never, statusCode: 200 });
  mockApi.getUserProfile.mockResolvedValue({ data: { contributor_role: { role: 'contributor' } } as never, statusCode: 200 });
  mockApi.getWalkthroughAccessTiers.mockResolvedValue({ data: { access_tiers: { 'wt-1': 'BUILDER' } }, statusCode: 200 });
  mockApi.getWalkthroughProgress.mockResolvedValue({ data: { progress: { status: 'not_started' } }, statusCode: 200 });

  render(<WalkthroughPageTemplate walkthrough={walkthrough} readme="# r" />);
  expect(await screen.findByTestId('detail')).toBeInTheDocument();
  expect(screen.queryByText('Upgrade to continue')).not.toBeInTheDocument();
  await waitFor(() => expect(mockApi.updateWalkthroughProgress).toHaveBeenCalledWith('wt-1', 'in_progress'));

  fireEvent.click(screen.getByText('mark-complete'));
  await waitFor(() => expect(mockApi.updateWalkthroughProgress).toHaveBeenCalledWith('wt-1', 'completed'));
});

it('keeps a past-due Builder without a contributor role locked', async () => {
  mockUseAuth.mockReturnValue({ isAuthenticated: true, isAdmin: false });
  mockApi.get.mockResolvedValue({ data: { membership_tier: 'BUILDER', subscription_status: 'past_due' } as never, statusCode: 200 });
  mockApi.getWalkthroughAccessTiers.mockResolvedValue({ data: { access_tiers: { 'wt-1': 'BUILDER' } }, statusCode: 200 });
  mockApi.getWalkthroughProgress.mockResolvedValue({ data: { progress: { status: 'not_started' } }, statusCode: 200 });

  render(<WalkthroughPageTemplate walkthrough={walkthrough} readme="# r" />);
  expect(await screen.findByText('Upgrade to continue')).toBeInTheDocument();
  expect(screen.queryByTestId('detail')).not.toBeInTheDocument();
  expect(mockApi.updateWalkthroughProgress).not.toHaveBeenCalled();
});

it('marks the walkthrough complete', async () => {
  mockUseAuth.mockReturnValue({ isAuthenticated: true, isAdmin: true });
  mockApi.get.mockResolvedValue({ data: { membership_tier: 'FREE' } as never, statusCode: 200 });
  mockApi.getWalkthroughAccessTiers.mockResolvedValue({ data: { access_tiers: {} }, statusCode: 200 });

  render(<WalkthroughPageTemplate walkthrough={walkthrough} readme="# r" />);
  const btn = await screen.findByText('mark-complete');
  fireEvent.click(btn);
  await waitFor(() => expect(mockApi.updateWalkthroughProgress).toHaveBeenCalledWith('wt-1', 'completed'));
});
