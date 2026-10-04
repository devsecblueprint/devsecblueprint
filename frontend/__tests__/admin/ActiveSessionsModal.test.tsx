/**
 * Unit tests for the admin ActiveSessionsModal.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { ActiveSessionsModal } from '@/components/admin/ActiveSessionsModal';

jest.mock('@/lib/api', () => ({ apiClient: { getActiveSessions: jest.fn() } }));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

const now = Math.floor(Date.now() / 1000);

beforeEach(() => jest.clearAllMocks());

it('shows active sessions after loading', async () => {
  mockApi.getActiveSessions.mockResolvedValue({
    data: {
      sessions: [
        { user_id: 'u1', username: 'ada', created_at: now - 3600, expires_at: now + 3600 },
        { user_id: 'u2', username: 'grace', created_at: now - 60, expires_at: now + 7200 },
      ],
      total_active: 2,
    },
    statusCode: 200,
  });
  render(<ActiveSessionsModal onClose={jest.fn()} />);
  expect(await screen.findByText('ada')).toBeInTheDocument();
  expect(screen.getByText('grace')).toBeInTheDocument();
  expect(screen.getByText('2 active')).toBeInTheDocument();
});

it('shows the empty state', async () => {
  mockApi.getActiveSessions.mockResolvedValue({ data: { sessions: [], total_active: 0 }, statusCode: 200 });
  render(<ActiveSessionsModal onClose={jest.fn()} />);
  expect(await screen.findByText(/No active sessions found/i)).toBeInTheDocument();
});

it('shows an error and retries', async () => {
  mockApi.getActiveSessions.mockResolvedValue({ error: 'boom', statusCode: 500 });
  render(<ActiveSessionsModal onClose={jest.fn()} />);
  expect(await screen.findByText('boom')).toBeInTheDocument();

  mockApi.getActiveSessions.mockResolvedValue({
    data: { sessions: [{ user_id: 'u1', username: 'ada', created_at: now, expires_at: now + 100 }], total_active: 1 },
    statusCode: 200,
  });
  fireEvent.click(screen.getByRole('button', { name: /retry/i }));
  expect(await screen.findByText('ada')).toBeInTheDocument();
});

it('closes via the Close button', async () => {
  const onClose = jest.fn();
  mockApi.getActiveSessions.mockResolvedValue({ data: { sessions: [], total_active: 0 }, statusCode: 200 });
  render(<ActiveSessionsModal onClose={onClose} />);
  await screen.findByText(/No active sessions found/i);
  fireEvent.click(screen.getByRole('button', { name: /^close$/i }));
  expect(onClose).toHaveBeenCalled();
});

it('closes on Escape', async () => {
  const onClose = jest.fn();
  mockApi.getActiveSessions.mockResolvedValue({ data: { sessions: [], total_active: 0 }, statusCode: 200 });
  render(<ActiveSessionsModal onClose={onClose} />);
  await screen.findByText(/No active sessions found/i);
  fireEvent.keyDown(document, { key: 'Escape' });
  expect(onClose).toHaveBeenCalled();
});
