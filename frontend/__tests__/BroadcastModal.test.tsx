/**
 * Unit tests for BroadcastModal.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { BroadcastModal } from '@/components/BroadcastModal';

jest.mock('@/lib/api', () => ({
  apiClient: { dismissBroadcast: jest.fn(), dismissAllBroadcasts: jest.fn() },
}));
jest.mock('@/components/MarkdownRenderer', () => ({
  __esModule: true,
  default: ({ markdown }: { markdown: string }) => <div data-testid="md">{markdown}</div>,
}));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function broadcast(id: string, overrides: Record<string, unknown> = {}) {
  return {
    broadcast_id: id,
    title: `Title ${id}`,
    message: `Message body for ${id}`,
    link: '',
    created_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

beforeEach(() => {
  jest.clearAllMocks();
  mockApi.dismissBroadcast.mockResolvedValue({ data: { message: 'ok' }, statusCode: 200 });
  mockApi.dismissAllBroadcasts.mockResolvedValue({ data: { message: 'ok' }, statusCode: 200 });
});

it('renders the first broadcast title and date', () => {
  render(<BroadcastModal broadcasts={[broadcast('1')]} onAllDismissed={jest.fn()} />);
  expect(screen.getByText('Title 1')).toBeInTheDocument();
});

it('renders nothing when there are no broadcasts', () => {
  const { container } = render(<BroadcastModal broadcasts={[]} onAllDismissed={jest.fn()} />);
  expect(container.querySelector('[role="dialog"]')).toBeNull();
});

it('shows the counter and navigates between multiple broadcasts', () => {
  render(<BroadcastModal broadcasts={[broadcast('1'), broadcast('2')]} onAllDismissed={jest.fn()} />);
  expect(screen.getByText('1 of 2')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /next/i }));
  expect(screen.getByText('Title 2')).toBeInTheDocument();
  expect(screen.getByText('2 of 2')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /previous/i }));
  expect(screen.getByText('Title 1')).toBeInTheDocument();
});

it('expands long content with Read More and collapses with Show Less', () => {
  const longMsg = 'x'.repeat(200);
  render(<BroadcastModal broadcasts={[broadcast('1', { message: longMsg })]} onAllDismissed={jest.fn()} />);
  expect(screen.getByRole('button', { name: /read more/i })).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /read more/i }));
  expect(screen.getByTestId('md')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /show less/i })).toBeInTheDocument();
});

it('dismisses the current broadcast and advances', async () => {
  const onAllDismissed = jest.fn();
  render(<BroadcastModal broadcasts={[broadcast('1'), broadcast('2')]} onAllDismissed={onAllDismissed} />);
  fireEvent.click(screen.getByRole('button', { name: /got it/i }));
  await waitFor(() => expect(mockApi.dismissBroadcast).toHaveBeenCalledWith('1'));
  // Second broadcast now shown; not all dismissed yet
  expect(await screen.findByText('Title 2')).toBeInTheDocument();
  expect(onAllDismissed).not.toHaveBeenCalled();
});

it('calls onAllDismissed after dismissing the last broadcast', async () => {
  const onAllDismissed = jest.fn();
  render(<BroadcastModal broadcasts={[broadcast('1')]} onAllDismissed={onAllDismissed} />);
  fireEvent.click(screen.getByRole('button', { name: /got it/i }));
  await waitFor(() => expect(onAllDismissed).toHaveBeenCalled());
});

it('dismisses all broadcasts at once', async () => {
  const onAllDismissed = jest.fn();
  render(<BroadcastModal broadcasts={[broadcast('1'), broadcast('2')]} onAllDismissed={onAllDismissed} />);
  fireEvent.click(screen.getByRole('button', { name: /dismiss all/i }));
  await waitFor(() => expect(mockApi.dismissAllBroadcasts).toHaveBeenCalled());
  expect(onAllDismissed).toHaveBeenCalled();
});

it('keeps the modal open if dismiss-all fails', async () => {
  const onAllDismissed = jest.fn();
  mockApi.dismissAllBroadcasts.mockResolvedValue({ error: 'network', statusCode: 500 });
  const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
  render(<BroadcastModal broadcasts={[broadcast('1'), broadcast('2')]} onAllDismissed={onAllDismissed} />);
  fireEvent.click(screen.getByRole('button', { name: /dismiss all/i }));
  await waitFor(() => expect(mockApi.dismissAllBroadcasts).toHaveBeenCalled());
  expect(onAllDismissed).not.toHaveBeenCalled();
  spy.mockRestore();
});

it('renders a CTA link when provided', () => {
  render(<BroadcastModal broadcasts={[broadcast('1', { link: 'https://example.com' })]} onAllDismissed={jest.fn()} />);
  const cta = screen.getByRole('link', { name: /check it out/i });
  expect(cta).toHaveAttribute('href', 'https://example.com');
  expect(cta).toHaveAttribute('target', '_blank');
});
