/**
 * Tests for the split BroadcastComposer / BroadcastHistory components.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { BroadcastComposer } from '@/components/admin/BroadcastComposer';
import { BroadcastHistory } from '@/components/admin/BroadcastHistory';

jest.mock('@/lib/api', () => ({
  apiClient: {
    getAdminBroadcasts: jest.fn(),
    createBroadcast: jest.fn(),
    deleteBroadcast: jest.fn(),
  },
}));
jest.mock('@/components/MarkdownRenderer', () => ({
  __esModule: true,
  default: ({ markdown }: { markdown: string }) => <div>{markdown}</div>,
}));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

const broadcast = (overrides: Record<string, unknown> = {}) => ({
  broadcast_id: 'b1',
  title: 'Hello',
  created_at: '2026-01-01T00:00:00Z',
  created_by: 'admin',
  ...overrides,
});

beforeEach(() => {
  jest.clearAllMocks();
  mockApi.getAdminBroadcasts.mockResolvedValue({ data: { broadcasts: [] }, statusCode: 200 });
});

describe('BroadcastHistory', () => {
  it('shows an Auto badge only for system:auto-announce broadcasts', async () => {
    mockApi.getAdminBroadcasts.mockResolvedValue({
      data: {
        broadcasts: [
          broadcast({ broadcast_id: 'a', title: 'Auto one', created_by: 'system:auto-announce' }),
          broadcast({ broadcast_id: 'm', title: 'Manual one', created_by: 'damien' }),
        ],
      } as never,
      statusCode: 200,
    });
    render(<BroadcastHistory />);
    await screen.findByText('Auto one');
    expect(screen.getAllByText('Auto')).toHaveLength(1);
    const autoRow = screen.getByText('Auto one').closest('div[class*="rounded-lg"]') as HTMLElement;
    expect(autoRow).toHaveTextContent('Auto');
    const manualRow = screen.getByText('Manual one').closest('div[class*="rounded-lg"]') as HTMLElement;
    expect(manualRow).not.toHaveTextContent(/^Auto/);
    expect(manualRow.querySelectorAll('span.rounded-full')).toHaveLength(0);
  });

  it('shows an error with Try Again that refetches', async () => {
    mockApi.getAdminBroadcasts.mockResolvedValueOnce({ error: 'boom', statusCode: 500 });
    render(<BroadcastHistory />);
    expect(await screen.findByText('boom')).toBeInTheDocument();
    mockApi.getAdminBroadcasts.mockResolvedValueOnce({ data: { broadcasts: [broadcast()] } as never, statusCode: 200 });
    fireEvent.click(screen.getByRole('button', { name: /try again/i }));
    expect(await screen.findByText('Hello')).toBeInTheDocument();
  });

  it('refetches when refreshKey changes', async () => {
    const { rerender } = render(<BroadcastHistory refreshKey={0} />);
    await screen.findByText(/No broadcasts sent yet/i);
    expect(mockApi.getAdminBroadcasts).toHaveBeenCalledTimes(1);
    rerender(<BroadcastHistory refreshKey={1} />);
    await waitFor(() => expect(mockApi.getAdminBroadcasts).toHaveBeenCalledTimes(2));
  });
});

describe('BroadcastComposer', () => {
  it('requires confirmation, sends, clears the form and calls onSent', async () => {
    mockApi.createBroadcast.mockResolvedValue({ data: { message: 'ok', broadcast: {} } as never, statusCode: 201 });
    const onSent = jest.fn();
    render(<BroadcastComposer onSent={onSent} />);
    fireEvent.change(screen.getByLabelText(/Title/i), { target: { value: 'Big News' } });
    fireEvent.change(screen.getByLabelText(/Message/i), { target: { value: 'Something' } });
    fireEvent.click(screen.getByRole('button', { name: /send broadcast/i }));
    expect(mockApi.createBroadcast).not.toHaveBeenCalled();
    fireEvent.click(await screen.findByRole('button', { name: /confirm send/i }));
    await waitFor(() => expect(mockApi.createBroadcast).toHaveBeenCalledWith('Big News', 'Something', undefined));
    expect(await screen.findByText(/Broadcast sent to all users/i)).toBeInTheDocument();
    expect(onSent).toHaveBeenCalledTimes(1);
    expect(screen.getByLabelText(/Title/i)).toHaveValue('');
  });

  it('does not call onSent when the send fails', async () => {
    mockApi.createBroadcast.mockResolvedValue({ error: 'rate limited', statusCode: 429 });
    const onSent = jest.fn();
    render(<BroadcastComposer onSent={onSent} />);
    fireEvent.change(screen.getByLabelText(/Title/i), { target: { value: 'T' } });
    fireEvent.change(screen.getByLabelText(/Message/i), { target: { value: 'M' } });
    fireEvent.click(screen.getByRole('button', { name: /send broadcast/i }));
    fireEvent.click(await screen.findByRole('button', { name: /confirm send/i }));
    expect(await screen.findByText('rate limited')).toBeInTheDocument();
    expect(onSent).not.toHaveBeenCalled();
  });
});
