/**
 * Unit tests for WalkthroughDetailClient.
 */
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { updateWalkthroughProgress } from '@/lib/walkthrough-client';
import { WalkthroughDetailClient } from '@/components/WalkthroughDetailClient';

const pushMock = jest.fn();
jest.mock('next/navigation', () => ({ useRouter: () => ({ push: pushMock }) }));
jest.mock('@/lib/api', () => ({ apiClient: { getWalkthroughProgress: jest.fn() } }));
jest.mock('@/lib/walkthrough-client', () => ({ updateWalkthroughProgress: jest.fn() }));
jest.mock('@/components/AuthGuard', () => ({ AuthGuard: ({ children }: { children: React.ReactNode }) => <>{children}</> }));
jest.mock('@/components/layout/NavbarWithAuth', () => ({ NavbarWithAuth: () => <nav /> }));
jest.mock('@/components/WalkthroughDetail', () => ({
  WalkthroughDetail: ({ walkthrough, onMarkComplete }: { walkthrough: { title: string; progress: { status: string } }; onMarkComplete: () => void }) => (
    <div>
      <span data-testid="status">{walkthrough.progress.status}</span>
      <span>{walkthrough.title}</span>
      <button onClick={onMarkComplete}>mark-complete</button>
    </div>
  ),
}));

const mockApi = apiClient as jest.Mocked<typeof apiClient>;
const mockUpdate = updateWalkthroughProgress as jest.Mock;

const walkthrough = { id: 'wt-1', title: 'AWS Lab' } as never;

beforeEach(() => jest.clearAllMocks());

it('shows a loading state then renders the detail with fetched progress', async () => {
  mockApi.getWalkthroughProgress.mockResolvedValue({
    data: { progress: { status: 'in_progress', started_at: '2026-01-01' } },
    statusCode: 200,
  });
  render(<WalkthroughDetailClient walkthrough={walkthrough} readme="# r" />);
  expect(screen.getByText(/Loading walkthrough/i)).toBeInTheDocument();
  await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('in_progress'));
  expect(screen.getByText('AWS Lab')).toBeInTheDocument();
});

it('defaults to not_started when no progress is returned', async () => {
  mockApi.getWalkthroughProgress.mockResolvedValue({ data: {} as never, statusCode: 200 });
  render(<WalkthroughDetailClient walkthrough={walkthrough} readme="# r" />);
  await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('not_started'));
});

it('defaults to not_started when the fetch throws', async () => {
  mockApi.getWalkthroughProgress.mockRejectedValue(new Error('x'));
  const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
  render(<WalkthroughDetailClient walkthrough={walkthrough} readme="# r" />);
  await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('not_started'));
  spy.mockRestore();
});

it('marks complete and navigates back on success', async () => {
  mockApi.getWalkthroughProgress.mockResolvedValue({
    data: { progress: { status: 'in_progress', started_at: '2026-01-01' } },
    statusCode: 200,
  });
  mockUpdate.mockResolvedValue({ success: true });
  render(<WalkthroughDetailClient walkthrough={walkthrough} readme="# r" />);
  await waitFor(() => expect(screen.getByText('mark-complete')).toBeInTheDocument());
  fireEvent.click(screen.getByText('mark-complete'));
  await waitFor(() => expect(mockUpdate).toHaveBeenCalledWith('wt-1', 'completed'));
  await waitFor(() => expect(pushMock).toHaveBeenCalledWith('/walkthroughs'));
});

it('alerts when mark-complete fails', async () => {
  mockApi.getWalkthroughProgress.mockResolvedValue({
    data: { progress: { status: 'in_progress', started_at: '2026-01-01' } },
    statusCode: 200,
  });
  mockUpdate.mockResolvedValue({ success: false, error: 'nope' });
  const alertSpy = jest.spyOn(window, 'alert').mockImplementation(() => {});
  render(<WalkthroughDetailClient walkthrough={walkthrough} readme="# r" />);
  await waitFor(() => expect(screen.getByText('mark-complete')).toBeInTheDocument());
  fireEvent.click(screen.getByText('mark-complete'));
  await waitFor(() => expect(alertSpy).toHaveBeenCalledWith('nope'));
  alertSpy.mockRestore();
});
