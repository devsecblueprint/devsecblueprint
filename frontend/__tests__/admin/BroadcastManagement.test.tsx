/**
 * Unit tests for admin BroadcastManagement.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { BroadcastManagement } from '@/components/admin/BroadcastManagement';

jest.mock('@/lib/api', () => ({
  apiClient: {
    getAdminBroadcasts: jest.fn(),
    createBroadcast: jest.fn(),
    deleteBroadcast: jest.fn(),
  },
}));
jest.mock('@/components/MarkdownRenderer', () => ({
  __esModule: true,
  default: ({ markdown }: { markdown: string }) => <div data-testid="md">{markdown}</div>,
}));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

beforeEach(() => {
  jest.clearAllMocks();
  mockApi.getAdminBroadcasts.mockResolvedValue({ data: { broadcasts: [] }, statusCode: 200 });
});

function fillCompose() {
  fireEvent.change(screen.getByLabelText(/Title/i), { target: { value: 'Big News' } });
  fireEvent.change(screen.getByLabelText(/Message/i), { target: { value: 'Something happened' } });
}

it('shows the empty history state', async () => {
  render(<BroadcastManagement />);
  expect(await screen.findByText(/No broadcasts sent yet/i)).toBeInTheDocument();
});

it('lists existing broadcasts', async () => {
  mockApi.getAdminBroadcasts.mockResolvedValue({
    data: { broadcasts: [{ broadcast_id: 'b1', title: 'Hello', created_at: '2026-01-01T00:00:00Z', created_by: 'admin' }] } as never,
    statusCode: 200,
  });
  render(<BroadcastManagement />);
  expect(await screen.findByText('Hello')).toBeInTheDocument();
});

it('validates a required title', async () => {
  render(<BroadcastManagement />);
  await screen.findByText(/No broadcasts sent yet/i);
  // message only, no title
  fireEvent.change(screen.getByLabelText(/Message/i), { target: { value: 'body' } });
  // Button is disabled without a title, so validation path is covered via the disabled state
  expect(screen.getByRole('button', { name: /send broadcast/i })).toBeDisabled();
});

it('toggles the markdown preview', async () => {
  render(<BroadcastManagement />);
  await screen.findByText(/No broadcasts sent yet/i);
  fireEvent.change(screen.getByLabelText(/Message/i), { target: { value: 'hello **world**' } });
  fireEvent.click(screen.getByRole('button', { name: /preview/i }));
  expect(screen.getByTestId('md')).toHaveTextContent('hello **world**');
});

it('requires confirmation and sends a broadcast', async () => {
  mockApi.createBroadcast.mockResolvedValue({ data: { message: 'ok', broadcast: {} } as never, statusCode: 201 });
  render(<BroadcastManagement />);
  await screen.findByText(/No broadcasts sent yet/i);
  fillCompose();
  fireEvent.click(screen.getByRole('button', { name: /send broadcast/i }));

  // Confirmation dialog appears
  expect(await screen.findByText(/send an email to all registered users/i)).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /confirm send/i }));

  await waitFor(() => expect(mockApi.createBroadcast).toHaveBeenCalledWith('Big News', 'Something happened', undefined));
  expect(await screen.findByText(/Broadcast sent to all users/i)).toBeInTheDocument();
});

it('surfaces a send error', async () => {
  mockApi.createBroadcast.mockResolvedValue({ error: 'rate limited', statusCode: 429 });
  render(<BroadcastManagement />);
  await screen.findByText(/No broadcasts sent yet/i);
  fillCompose();
  fireEvent.click(screen.getByRole('button', { name: /send broadcast/i }));
  fireEvent.click(await screen.findByRole('button', { name: /confirm send/i }));
  expect(await screen.findByText('rate limited')).toBeInTheDocument();
});

it('deletes a broadcast after confirmation', async () => {
  mockApi.getAdminBroadcasts.mockResolvedValue({
    data: { broadcasts: [{ broadcast_id: 'b1', title: 'Hello', created_at: '2026-01-01T00:00:00Z', created_by: 'admin' }] } as never,
    statusCode: 200,
  });
  mockApi.deleteBroadcast.mockResolvedValue({ data: { message: 'ok' }, statusCode: 200 });
  jest.spyOn(window, 'confirm').mockReturnValue(true);

  render(<BroadcastManagement />);
  await screen.findByText('Hello');
  fireEvent.click(screen.getByRole('button', { name: /^delete$/i }));
  await waitFor(() => expect(mockApi.deleteBroadcast).toHaveBeenCalledWith('b1'));
  await waitFor(() => expect(screen.queryByText('Hello')).not.toBeInTheDocument());
});

it('does not delete when confirmation is cancelled', async () => {
  mockApi.getAdminBroadcasts.mockResolvedValue({
    data: { broadcasts: [{ broadcast_id: 'b1', title: 'Hello', created_at: '2026-01-01T00:00:00Z', created_by: 'admin' }] } as never,
    statusCode: 200,
  });
  jest.spyOn(window, 'confirm').mockReturnValue(false);
  render(<BroadcastManagement />);
  await screen.findByText('Hello');
  fireEvent.click(screen.getByRole('button', { name: /^delete$/i }));
  expect(mockApi.deleteBroadcast).not.toHaveBeenCalled();
});
