/**
 * Unit tests for CapstonePageGate.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { useAuth } from '@/lib/hooks/useAuth';
import { apiClient } from '@/lib/api';
import { CapstonePageGate } from '@/components/CapstonePageGate';

jest.mock('@/lib/hooks/useAuth', () => ({ useAuth: jest.fn() }));
jest.mock('@/lib/api', () => ({ apiClient: { get: jest.fn(), getUserProfile: jest.fn() } }));
const mockUseAuth = useAuth as jest.Mock;
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function Child() {
  return <div data-testid="gated-content">Secret capstone content</div>;
}

function renderGate() {
  return render(
    <CapstonePageGate title="Capstone X" description="Build something">
      <Child />
    </CapstonePageGate>,
  );
}

beforeEach(() => jest.clearAllMocks());

it('grants access to admins immediately', async () => {
  mockUseAuth.mockReturnValue({ isAuthenticated: true, isAdmin: true });
  renderGate();
  expect(await screen.findByTestId('gated-content')).toBeInTheDocument();
});

it('grants access to active Builder subscribers', async () => {
  mockUseAuth.mockReturnValue({ isAuthenticated: true, isAdmin: false });
  mockApi.get.mockResolvedValue({
    data: { membership_tier: 'BUILDER', subscription_status: 'active' } as never,
    statusCode: 200,
  });
  renderGate();
  expect(await screen.findByTestId('gated-content')).toBeInTheDocument();
});

it('grants access to contributors without a subscription', async () => {
  mockUseAuth.mockReturnValue({ isAuthenticated: true, isAdmin: false });
  mockApi.get.mockResolvedValue({ data: { subscription_status: 'inactive' } as never, statusCode: 200 });
  mockApi.getUserProfile.mockResolvedValue({ data: { contributor_role: { role: 'author' } } as never, statusCode: 200 });
  renderGate();
  expect(await screen.findByTestId('gated-content')).toBeInTheDocument();
});

it('shows the locked upgrade prompt for free-tier users', async () => {
  mockUseAuth.mockReturnValue({ isAuthenticated: true, isAdmin: false });
  mockApi.get.mockResolvedValue({ data: { subscription_status: 'inactive' } as never, statusCode: 200 });
  mockApi.getUserProfile.mockResolvedValue({ data: { contributor_role: null } as never, statusCode: 200 });
  renderGate();
  expect(await screen.findByText('Capstone Project Locked')).toBeInTheDocument();
  expect(screen.getByText('Capstone X')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /upgrade to builder/i })).toHaveAttribute('href', '/pricing');
  expect(screen.queryByTestId('gated-content')).not.toBeInTheDocument();
});

it('shows the locked state for unauthenticated users', async () => {
  mockUseAuth.mockReturnValue({ isAuthenticated: false, isAdmin: false });
  renderGate();
  expect(await screen.findByText('Capstone Project Locked')).toBeInTheDocument();
});
