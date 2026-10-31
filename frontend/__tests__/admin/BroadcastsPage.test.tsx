/**
 * Tests for the /admin/broadcasts page (auth gating, tabs, keyboard navigation).
 */
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { useAuth } from '@/lib/hooks/useAuth';
import { apiClient } from '@/lib/api';
import AdminBroadcastsPage from '@/app/admin/broadcasts/page';

const mockPush = jest.fn();
jest.mock('next/navigation', () => ({ useRouter: () => ({ push: mockPush }) }));
jest.mock('@/lib/hooks/useAuth', () => ({ useAuth: jest.fn() }));
jest.mock('@/components/layout/NavbarWithAuth', () => ({ NavbarWithAuth: () => <nav data-testid="navbar" /> }));
jest.mock('@/components/AuthGuard', () => ({ AuthGuard: ({ children }: { children: React.ReactNode }) => <>{children}</> }));
jest.mock('@/components/MarkdownRenderer', () => ({
  __esModule: true,
  default: ({ markdown }: { markdown: string }) => <div>{markdown}</div>,
}));
jest.mock('@/lib/api', () => ({
  apiClient: {
    getAdminBroadcasts: jest.fn(),
    createBroadcast: jest.fn(),
    deleteBroadcast: jest.fn(),
    getAnnouncements: jest.fn(),
    retryAnnouncement: jest.fn(),
    baselineAnnouncements: jest.fn(),
  },
}));

const mockAuth = useAuth as jest.Mock;
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

beforeEach(() => {
  jest.clearAllMocks();
  mockApi.getAdminBroadcasts.mockResolvedValue({ data: { broadcasts: [] }, statusCode: 200 });
  mockApi.getAnnouncements.mockResolvedValue({
    data: { enabled: true, failed_count: 0, announcements: [] },
    statusCode: 200,
  });
});

afterEach(() => {
  jest.useRealTimers();
});

describe('access control', () => {
  it('shows the 403 screen to non-admin users and redirects to the dashboard', () => {
    jest.useFakeTimers();
    mockAuth.mockReturnValue({ isAdmin: false, isAuthenticated: true, isLoading: false });
    render(<AdminBroadcastsPage />);
    expect(screen.getByText(/403 - Access Denied/i)).toBeInTheDocument();
    expect(screen.queryByRole('tablist')).not.toBeInTheDocument();
    act(() => {
      jest.advanceTimersByTime(2000);
    });
    expect(mockPush).toHaveBeenCalledWith('/dashboard');
  });

  it('renders nothing for unauthenticated users', () => {
    mockAuth.mockReturnValue({ isAdmin: false, isAuthenticated: false, isLoading: false });
    const { container } = render(<AdminBroadcastsPage />);
    expect(container).toBeEmptyDOMElement();
  });
});

describe('admin view', () => {
  beforeEach(() => {
    mockAuth.mockReturnValue({ isAdmin: true, isAuthenticated: true, isLoading: false });
  });

  it('shows the header, back link and three tabs', async () => {
    render(<AdminBroadcastsPage />);
    expect(screen.getByRole('heading', { level: 1, name: 'Broadcasts' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /back to admin dashboard/i })).toHaveAttribute('href', '/admin');
    const tabs = screen.getAllByRole('tab');
    expect(tabs.map((t) => t.textContent)).toEqual(['Compose', 'History', 'Automation']);
    expect(tabs[0]).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByLabelText(/Title/i)).toBeInTheDocument();
  });

  it('switches panels on click and links tabs to panels via aria-controls', async () => {
    render(<AdminBroadcastsPage />);
    const historyTab = screen.getByRole('tab', { name: 'History' });
    fireEvent.click(historyTab);
    expect(historyTab).toHaveAttribute('aria-selected', 'true');
    expect(await screen.findByText(/No broadcasts sent yet/i)).toBeInTheDocument();
    const panel = document.getElementById(historyTab.getAttribute('aria-controls')!);
    expect(panel).toHaveAttribute('role', 'tabpanel');
    expect(panel).toContainElement(screen.getByText(/No broadcasts sent yet/i));

    fireEvent.click(screen.getByRole('tab', { name: 'Automation' }));
    expect(await screen.findByText(/No announcements yet/i)).toBeInTheDocument();
  });

  it('supports roving tabindex and arrow/Home/End keyboard navigation', async () => {
    render(<AdminBroadcastsPage />);
    const [compose, history, automation] = screen.getAllByRole('tab');
    expect(compose).toHaveAttribute('tabindex', '0');
    expect(history).toHaveAttribute('tabindex', '-1');

    compose.focus();
    fireEvent.keyDown(compose, { key: 'ArrowRight' });
    expect(history).toHaveAttribute('aria-selected', 'true');
    expect(history).toHaveFocus();

    fireEvent.keyDown(history, { key: 'End' });
    expect(automation).toHaveAttribute('aria-selected', 'true');
    expect(automation).toHaveFocus();

    // ArrowRight wraps from the last tab to the first
    fireEvent.keyDown(automation, { key: 'ArrowRight' });
    expect(compose).toHaveAttribute('aria-selected', 'true');

    // ArrowLeft wraps from the first tab to the last
    fireEvent.keyDown(compose, { key: 'ArrowLeft' });
    expect(automation).toHaveAttribute('aria-selected', 'true');

    fireEvent.keyDown(automation, { key: 'Home' });
    expect(compose).toHaveAttribute('aria-selected', 'true');
    await waitFor(() => expect(compose).toHaveFocus());
  });

  it('switches to History and shows the new broadcast after a successful send', async () => {
    mockApi.createBroadcast.mockResolvedValue({ data: { message: 'ok', broadcast: {} } as never, statusCode: 201 });
    render(<AdminBroadcastsPage />);
    fireEvent.change(screen.getByLabelText(/Title/i), { target: { value: 'Big News' } });
    fireEvent.change(screen.getByLabelText(/Message/i), { target: { value: 'Body' } });
    fireEvent.click(screen.getByRole('button', { name: /send broadcast/i }));

    mockApi.getAdminBroadcasts.mockResolvedValue({
      data: {
        broadcasts: [{ broadcast_id: 'b9', title: 'Big News', created_at: '2026-01-01T00:00:00Z', created_by: 'admin' }],
      } as never,
      statusCode: 200,
    });
    fireEvent.click(await screen.findByRole('button', { name: /confirm send/i }));

    await waitFor(() => expect(screen.getByRole('tab', { name: 'History' })).toHaveAttribute('aria-selected', 'true'));
    expect(await screen.findByText('Big News')).toBeInTheDocument();
  });
});
