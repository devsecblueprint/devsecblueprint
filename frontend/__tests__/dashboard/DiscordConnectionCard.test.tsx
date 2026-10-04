/**
 * Unit tests for DiscordConnectionCard.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { DiscordConnectionCard } from '@/components/dashboard/DiscordConnectionCard';

jest.mock('@/lib/api', () => ({ apiClient: { get: jest.fn(), delete: jest.fn() } }));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function status(overrides: Record<string, unknown> = {}) {
  return {
    connected: true,
    discord_username: 'ada#1234',
    discord_avatar_url: null,
    discord_roles: [],
    platform_state: 'Roles_Synced',
    last_synced_at: null,
    last_sync_status: null,
    ...overrides,
  };
}

beforeEach(() => jest.clearAllMocks());

it('shows the connected state with username and synced status', async () => {
  mockApi.get.mockResolvedValue({ data: status(), statusCode: 200 });
  render(<DiscordConnectionCard />);
  expect(await screen.findByText('ada#1234')).toBeInTheDocument();
  expect(screen.getByText('Connected')).toBeInTheDocument();
  expect(screen.getByText('✓ Roles synced')).toBeInTheDocument();
});

it('renders assigned roles', async () => {
  mockApi.get.mockResolvedValue({
    data: status({ discord_roles: [{ name: 'Builder', color: '#ffbe00' }, { name: 'Member', color: null }] }),
    statusCode: 200,
  });
  render(<DiscordConnectionCard />);
  expect(await screen.findByText('Builder')).toBeInTheDocument();
  expect(screen.getByText('Member')).toBeInTheDocument();
});

it('shows "No roles assigned" when there are none', async () => {
  mockApi.get.mockResolvedValue({ data: status({ discord_roles: [] }), statusCode: 200 });
  render(<DiscordConnectionCard />);
  expect(await screen.findByText('No roles assigned')).toBeInTheDocument();
});

it('shows the not-connected state with a connect button', async () => {
  mockApi.get.mockResolvedValue({ data: status({ connected: false }), statusCode: 200 });
  render(<DiscordConnectionCard />);
  expect(await screen.findByRole('button', { name: /connect discord/i })).toBeInTheDocument();
});

it('shows a neutral error message when status fails', async () => {
  mockApi.get.mockResolvedValue({ error: 'boom', statusCode: 500 });
  render(<DiscordConnectionCard />);
  expect(await screen.findByText(/Unable to load Discord status/i)).toBeInTheDocument();
});

it('disconnects and refetches', async () => {
  mockApi.get
    .mockResolvedValueOnce({ data: status(), statusCode: 200 })
    .mockResolvedValueOnce({ data: status({ connected: false }), statusCode: 200 });
  mockApi.delete.mockResolvedValue({ data: { message: 'ok' }, statusCode: 200 });

  render(<DiscordConnectionCard />);
  const disconnect = await screen.findByRole('button', { name: /disconnect discord account/i });
  fireEvent.click(disconnect);

  await waitFor(() => expect(mockApi.delete).toHaveBeenCalledWith('/api/discord/disconnect'));
  expect(await screen.findByRole('button', { name: /connect discord/i })).toBeInTheDocument();
});
