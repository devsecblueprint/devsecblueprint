/**
 * Unit tests for AdminUserDiscordPanel.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { AdminUserDiscordPanel } from '@/components/admin/AdminUserDiscordPanel';

jest.mock('@/lib/api', () => ({ apiClient: { get: jest.fn(), post: jest.fn(), delete: jest.fn() } }));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function userInfo(overrides: Record<string, unknown> = {}) {
  return {
    discord_connected: true,
    discord_username: 'ada#1',
    discord_user_id: '123',
    platform_state: 'Roles_Synced',
    membership_tier: 'BUILDER',
    stripe_subscription_status: 'active',
    last_synced_at: '2026-01-01T00:00:00Z',
    last_sync_status: 'success',
    platform_roles: ['Builder'],
    ...overrides,
  };
}

/** Default both info + audit fetches. */
function setupFetch(info = userInfo(), audit: unknown[] = []) {
  mockApi.get.mockImplementation((url: string) => {
    if (url.includes('/audit')) return Promise.resolve({ data: { audit_log: audit }, statusCode: 200 });
    return Promise.resolve({ data: info as never, statusCode: 200 });
  });
}

beforeEach(() => jest.clearAllMocks());

it('renders Discord + subscription info', async () => {
  setupFetch();
  render(<AdminUserDiscordPanel userId="u1" />);
  expect(await screen.findByText('ada#1')).toBeInTheDocument();
  expect(screen.getByText('Connected')).toBeInTheDocument();
  expect(screen.getByText('BUILDER')).toBeInTheDocument();
  expect(screen.getByText('No audit entries found.')).toBeInTheDocument();
});

it('renders the audit log entries', async () => {
  setupFetch(userInfo(), [
    { event_type: 'discord_connected', timestamp: '2026-01-01T00:00:00Z', actor: 'admin', reason: 'manual' },
  ]);
  render(<AdminUserDiscordPanel userId="u1" />);
  expect(await screen.findByText('Discord Connected')).toBeInTheDocument();
  expect(screen.getByText('by admin')).toBeInTheDocument();
});

it('shows a friendly message on a 404', async () => {
  mockApi.get.mockImplementation((url: string) => {
    if (url.includes('/audit')) return Promise.resolve({ data: { audit_log: [] }, statusCode: 200 });
    return Promise.resolve({ error: 'HTTP 404: Not Found', statusCode: 404 });
  });
  render(<AdminUserDiscordPanel userId="u1" />);
  expect(await screen.findByText(/Discord not connected/i)).toBeInTheDocument();
});

it('validates the disconnect reason length', async () => {
  setupFetch();
  render(<AdminUserDiscordPanel userId="u1" />);
  await screen.findByText('ada#1');
  // Disconnect button is disabled when reason < 5 chars
  const disconnectBtn = screen.getByRole('button', { name: /^disconnect$/i });
  expect(disconnectBtn).toBeDisabled();
  fireEvent.change(screen.getByLabelText(/Disconnect Reason/i), { target: { value: 'valid reason' } });
  expect(disconnectBtn).toBeEnabled();
});

it('disconnects with a valid reason', async () => {
  setupFetch();
  mockApi.delete.mockResolvedValue({ data: { message: 'ok' }, statusCode: 200 });
  render(<AdminUserDiscordPanel userId="u1" />);
  await screen.findByText('ada#1');
  fireEvent.change(screen.getByLabelText(/Disconnect Reason/i), { target: { value: 'spam account' } });
  fireEvent.click(screen.getByRole('button', { name: /^disconnect$/i }));
  await waitFor(() => expect(mockApi.delete).toHaveBeenCalledWith('/admin/discord/users/u1/disconnect'));
  expect(await screen.findByText(/disconnected successfully/i)).toBeInTheDocument();
});

it('triggers a sync', async () => {
  setupFetch();
  mockApi.post.mockResolvedValue({ data: { message: 'ok' }, statusCode: 200 });
  render(<AdminUserDiscordPanel userId="u1" />);
  await screen.findByText('ada#1');
  fireEvent.click(screen.getByRole('button', { name: /trigger sync/i }));
  await waitFor(() => expect(mockApi.post).toHaveBeenCalledWith('/admin/discord/users/u1/sync', {}));
  expect(await screen.findByText(/Sync triggered successfully/i)).toBeInTheDocument();
});
