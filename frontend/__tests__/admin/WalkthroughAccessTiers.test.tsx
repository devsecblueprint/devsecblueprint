/**
 * Unit tests for admin WalkthroughAccessTiers.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { WalkthroughAccessTiers } from '@/components/admin/WalkthroughAccessTiers';
import { WALKTHROUGHS_DATA } from '@/lib/walkthroughs-data';

jest.mock('@/lib/api', () => ({
  apiClient: { getAdminWalkthroughAccessTiers: jest.fn(), setWalkthroughAccessTier: jest.fn() },
}));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

const firstWt = WALKTHROUGHS_DATA[0];

beforeEach(() => jest.clearAllMocks());

it('renders all walkthroughs with their tiers', async () => {
  mockApi.getAdminWalkthroughAccessTiers.mockResolvedValue({
    data: { access_tiers: { [firstWt.id]: 'BUILDER' } },
    statusCode: 200,
  });
  render(<WalkthroughAccessTiers />);
  expect(await screen.findByText(firstWt.title)).toBeInTheDocument();
  expect(screen.getByText(/of .* walkthroughs locked to Builder/i)).toBeInTheDocument();
});

it('defaults missing tiers to FREE', async () => {
  mockApi.getAdminWalkthroughAccessTiers.mockResolvedValue({ data: { access_tiers: {} }, statusCode: 200 });
  render(<WalkthroughAccessTiers />);
  await screen.findByText(firstWt.title);
  // Count the Free labels — there should be at least one
  expect(screen.getAllByText('Free').length).toBeGreaterThan(0);
});

it('shows error state with retry', async () => {
  mockApi.getAdminWalkthroughAccessTiers.mockResolvedValue({ error: 'boom', statusCode: 500 });
  render(<WalkthroughAccessTiers />);
  expect(await screen.findByText('boom')).toBeInTheDocument();
  mockApi.getAdminWalkthroughAccessTiers.mockResolvedValue({ data: { access_tiers: {} }, statusCode: 200 });
  fireEvent.click(screen.getByRole('button', { name: /try again/i }));
  expect(await screen.findByText(firstWt.title)).toBeInTheDocument();
});

it('toggles a tier optimistically and persists', async () => {
  mockApi.getAdminWalkthroughAccessTiers.mockResolvedValue({ data: { access_tiers: {} }, statusCode: 200 });
  mockApi.setWalkthroughAccessTier.mockResolvedValue({ data: { message: 'ok', data: {} } as never, statusCode: 200 });
  render(<WalkthroughAccessTiers />);
  await screen.findByText(firstWt.title);

  const toggle = screen.getByRole('switch', { name: new RegExp(firstWt.title) });
  expect(toggle).toHaveAttribute('aria-checked', 'false');
  fireEvent.click(toggle);
  await waitFor(() => expect(mockApi.setWalkthroughAccessTier).toHaveBeenCalledWith(firstWt.id, 'BUILDER'));
  expect(toggle).toHaveAttribute('aria-checked', 'true');
});

it('reverts the toggle when the API call fails', async () => {
  mockApi.getAdminWalkthroughAccessTiers.mockResolvedValue({ data: { access_tiers: {} }, statusCode: 200 });
  mockApi.setWalkthroughAccessTier.mockResolvedValue({ error: 'denied', statusCode: 500 });
  render(<WalkthroughAccessTiers />);
  await screen.findByText(firstWt.title);

  const toggle = screen.getByRole('switch', { name: new RegExp(firstWt.title) });
  fireEvent.click(toggle);
  await waitFor(() => expect(mockApi.setWalkthroughAccessTier).toHaveBeenCalled());
  // Reverted back to FREE
  await waitFor(() => expect(toggle).toHaveAttribute('aria-checked', 'false'));
});
