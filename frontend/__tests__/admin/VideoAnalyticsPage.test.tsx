/**
 * Tests for the /admin/videos/analytics page (auth gating) and the links to it.
 */
import { render, screen, act, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { useAuth } from '@/lib/hooks/useAuth';
import AdminVideoAnalyticsPage from '@/app/admin/videos/analytics/page';
import AdminVideosPage from '@/app/admin/videos/page';
import AdminDashboardPage from '@/app/admin/page';

const mockPush = jest.fn();
jest.mock('next/navigation', () => ({ useRouter: () => ({ push: mockPush }) }));
jest.mock('@/lib/hooks/useAuth', () => ({ useAuth: jest.fn() }));
jest.mock('@/components/layout/NavbarWithAuth', () => ({ NavbarWithAuth: () => <nav data-testid="navbar" /> }));
jest.mock('@/components/AuthGuard', () => ({ AuthGuard: ({ children }: { children: React.ReactNode }) => <>{children}</> }));
jest.mock('@/lib/api', () => ({
  apiClient: { getVideoAnalytics: jest.fn(), getAnnouncements: jest.fn(), post: jest.fn() },
}));
jest.mock('@/lib/video-client', () => ({
  adminListVideos: jest.fn().mockResolvedValue({ data: { recordings: [], totalCount: 0 } }),
  adminCreateVideo: jest.fn(),
  adminUpdateVideo: jest.fn(),
  adminTransitionStatus: jest.fn(),
}));
jest.mock('@/components/admin/ActiveSessionsModal', () => ({ ActiveSessionsModal: () => null }));
jest.mock('@/app/admin/components/AdminDashboardProvider', () => ({
  AdminDashboardProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAdminContext: () => ({ analytics: null }),
}));
jest.mock('@/app/admin/components/PlatformSummary', () => ({ PlatformSummary: () => null }));
jest.mock('@/app/admin/components/RegistrationAnalytics', () => ({ RegistrationAnalytics: () => null }));
jest.mock('@/app/admin/components/NeedsAttentionPanel', () => ({ NeedsAttentionPanel: () => null }));
jest.mock('@/app/admin/components/ActivitySection', () => ({ ActivitySection: () => null }));
jest.mock('@/app/admin/components/JourneyAnalyticsSection', () => ({ JourneyAnalyticsSection: () => null }));
jest.mock('@/app/admin/components/DangerZone', () => ({ DangerZone: () => null }));
jest.mock('@/app/admin/components/AdministrativeTools', () => ({ AdministrativeTools: () => null }));

const mockAuth = useAuth as jest.Mock;
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

const ANALYTICS = {
  generated_at: new Date().toISOString(),
  stale: false,
  totals: { distinct_viewers: 3, active_7d: 2, active_30d: 3, completions: 1, completion_rate: 33 },
  by_tier: {
    FREE: { viewers: 3, completions: 1, completion_rate: 33 },
    BUILDER: { viewers: 0, completions: 0, completion_rate: 0 },
  },
  top_videos: [],
  videos: [
    {
      id: 'v1',
      title: 'Only Video',
      slug: 'only-video',
      status: 'PUBLISHED' as const,
      access_tier: 'FREE' as const,
      unique_viewers: 3,
      completed: 1,
      completion_rate: 33,
      avg_best_progress: 50,
      last_watched_at: null,
    },
  ],
};

beforeEach(() => {
  jest.clearAllMocks();
  mockApi.getVideoAnalytics.mockResolvedValue({ data: ANALYTICS, statusCode: 200 });
  mockApi.getAnnouncements.mockResolvedValue({
    data: { enabled: true, failed_count: 0, announcements: [] },
    statusCode: 200,
  });
});

afterEach(() => {
  jest.useRealTimers();
});

describe('access control', () => {
  it('shows the 403 screen to non-admin users and does not load analytics', () => {
    jest.useFakeTimers();
    mockAuth.mockReturnValue({ isAdmin: false, isAuthenticated: true, isLoading: false });
    render(<AdminVideoAnalyticsPage />);
    expect(screen.getByText(/403 - Access Denied/i)).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Video Analytics' })).not.toBeInTheDocument();
    expect(mockApi.getVideoAnalytics).not.toHaveBeenCalled();
    act(() => {
      jest.advanceTimersByTime(2000);
    });
    expect(mockPush).toHaveBeenCalledWith('/dashboard');
  });

  it('renders nothing for unauthenticated users', () => {
    mockAuth.mockReturnValue({ isAdmin: false, isAuthenticated: false, isLoading: false });
    const { container } = render(<AdminVideoAnalyticsPage />);
    expect(container).toBeEmptyDOMElement();
    expect(mockApi.getVideoAnalytics).not.toHaveBeenCalled();
  });
});

describe('admin view', () => {
  beforeEach(() => {
    mockAuth.mockReturnValue({ isAdmin: true, isAuthenticated: true, isLoading: false });
  });

  it('renders the header, back link and the analytics component', async () => {
    render(<AdminVideoAnalyticsPage />);
    expect(screen.getByRole('heading', { level: 1, name: 'Video Analytics' })).toBeInTheDocument();
    expect(screen.getByText('How members watch the Video Library')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /back to videos/i })).toHaveAttribute('href', '/admin/videos');
    expect(await screen.findByRole('table')).toBeInTheDocument();
    expect(screen.getByText('Only Video', { selector: 'th' })).toBeInTheDocument();
    expect(mockApi.getVideoAnalytics).toHaveBeenCalledTimes(1);
  });
});

describe('links to the analytics page', () => {
  beforeEach(() => {
    mockAuth.mockReturnValue({ isAdmin: true, isAuthenticated: true, isLoading: false });
  });

  it('is linked from the videos admin page header', async () => {
    render(<AdminVideosPage />);
    expect(await screen.findByRole('link', { name: 'Analytics' })).toHaveAttribute(
      'href',
      '/admin/videos/analytics'
    );  });

  it('is linked from the Video Management card on the dashboard', async () => {
    render(<AdminDashboardPage />);
    expect(screen.getByRole('link', { name: 'View Analytics' })).toHaveAttribute(
      'href',
      '/admin/videos/analytics'
    );
    expect(screen.getByRole('link', { name: 'Manage Videos' })).toHaveAttribute('href', '/admin/videos');
    await waitFor(() => expect(mockApi.getAnnouncements).toHaveBeenCalled());
  });
});
