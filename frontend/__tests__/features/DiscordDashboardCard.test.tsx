/**
 * Unit tests for DiscordDashboardCard.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { DiscordDashboardCard } from '@/components/features/DiscordDashboardCard';

jest.mock('@/lib/api', () => ({ apiClient: { get: jest.fn() } }));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

beforeEach(() => jest.clearAllMocks());

it('shows a spinner while loading', () => {
  mockApi.get.mockReturnValue(new Promise(() => {}));
  const { container } = render(<DiscordDashboardCard />);
  expect(container.querySelector('.animate-spin')).toBeInTheDocument();
});

it('shows the connected state with username', async () => {
  mockApi.get.mockResolvedValue({ data: { connected: true, discord_username: 'ada#1' } as never, statusCode: 200 });
  render(<DiscordDashboardCard />);
  expect(await screen.findByText('Discord Connected')).toBeInTheDocument();
  expect(screen.getByText('ada#1')).toBeInTheDocument();
});

it('shows a connect button when not connected', async () => {
  mockApi.get.mockResolvedValue({ data: { connected: false } as never, statusCode: 200 });
  render(<DiscordDashboardCard />);
  expect(await screen.findByRole('button', { name: /connect discord/i })).toBeInTheDocument();
});

it('shows a neutral message on error', async () => {
  mockApi.get.mockResolvedValue({ error: 'boom', statusCode: 500 });
  render(<DiscordDashboardCard />);
  expect(await screen.findByText(/Unable to load Discord status/i)).toBeInTheDocument();
});
