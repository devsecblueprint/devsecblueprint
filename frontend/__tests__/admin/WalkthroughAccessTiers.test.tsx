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

it('shows Default captions, help text and counts for a BUILDER default', async () => {
  mockApi.getAdminWalkthroughAccessTiers.mockResolvedValue({
    data: { access_tiers: { [firstWt.id]: 'FREE' }, default_tier: 'BUILDER' },
    statusCode: 200,
  });
  render(<WalkthroughAccessTiers />);
  await screen.findByText(firstWt.title);
  const total = WALKTHROUGHS_DATA.length;
  expect(screen.getByText('New walkthroughs start as Builder until you set them to Free.')).toBeInTheDocument();
  // Every row except the explicit FREE one is a default row
  expect(screen.getAllByText('Default')).toHaveLength(total - 1);
  expect(screen.getByText(`${total - 1} of ${total} walkthroughs locked to Builder`)).toBeInTheDocument();
  expect(screen.getByRole('switch', { name: new RegExp(firstWt.title) })).toHaveAttribute('aria-checked', 'false');
});

it('hides the help text and treats a missing default_tier as FREE', async () => {
  mockApi.getAdminWalkthroughAccessTiers.mockResolvedValue({
    data: { access_tiers: { [firstWt.id]: 'BUILDER' } },
    statusCode: 200,
  });
  render(<WalkthroughAccessTiers />);
  await screen.findByText(firstWt.title);
  expect(screen.queryByText(/New walkthroughs start as Builder/)).not.toBeInTheDocument();
  expect(screen.getByText(`1 of ${WALKTHROUGHS_DATA.length} walkthroughs locked to Builder`)).toBeInTheDocument();
});

it('toggles a default-BUILDER row to FREE, persists FREE and clears the Default caption', async () => {
  mockApi.getAdminWalkthroughAccessTiers.mockResolvedValue({ data: { access_tiers: {}, default_tier: 'BUILDER' }, statusCode: 200 });
  mockApi.setWalkthroughAccessTier.mockResolvedValue({ data: { message: 'ok', data: {} } as never, statusCode: 200 });
  render(<WalkthroughAccessTiers />);
  await screen.findByText(firstWt.title);
  const total = WALKTHROUGHS_DATA.length;
  const toggle = screen.getByRole('switch', { name: new RegExp(firstWt.title) });
  expect(toggle).toHaveAttribute('aria-checked', 'true');
  fireEvent.click(toggle);
  await waitFor(() => expect(mockApi.setWalkthroughAccessTier).toHaveBeenCalledWith(firstWt.id, 'FREE'));
  expect(toggle).toHaveAttribute('aria-checked', 'false');
  expect(screen.getAllByText('Default')).toHaveLength(total - 1);
});

it('restores tier and Default caption when toggling a default row fails', async () => {
  mockApi.getAdminWalkthroughAccessTiers.mockResolvedValue({ data: { access_tiers: {}, default_tier: 'BUILDER' }, statusCode: 200 });
  mockApi.setWalkthroughAccessTier.mockResolvedValue({ error: 'denied', statusCode: 500 });
  render(<WalkthroughAccessTiers />);
  await screen.findByText(firstWt.title);
  const toggle = screen.getByRole('switch', { name: new RegExp(firstWt.title) });
  fireEvent.click(toggle);
  await waitFor(() => expect(toggle).toHaveAttribute('aria-checked', 'true'));
  expect(screen.getAllByText('Default')).toHaveLength(WALKTHROUGHS_DATA.length);
});
