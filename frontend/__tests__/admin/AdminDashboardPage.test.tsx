/**
 * Dashboard page tests: Broadcasts launcher card, Active Sessions KPI, and navigation targets.
 */
import fs from 'fs';
import path from 'path';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { useAuth } from '@/lib/hooks/useAuth';
import AdminDashboardPage from '@/app/admin/page';

jest.mock('next/navigation', () => ({ useRouter: () => ({ push: jest.fn() }) }));
jest.mock('@/lib/hooks/useAuth', () => ({ useAuth: jest.fn() }));
jest.mock('@/components/layout/NavbarWithAuth', () => ({ NavbarWithAuth: () => <nav /> }));
jest.mock('@/components/AuthGuard', () => ({ AuthGuard: ({ children }: { children: React.ReactNode }) => <>{children}</> }));
jest.mock('@/lib/api', () => ({
  apiClient: { getAnnouncements: jest.fn(), post: jest.fn() },
}));
jest.mock('@/components/admin/ActiveSessionsModal', () => ({
  ActiveSessionsModal: ({ onClose }: { onClose: () => void }) => (
    <div role="dialog" aria-label="Active Sessions Modal">
      <button onClick={onClose}>close-sessions</button>
    </div>
  ),
}));

// Lightweight provider that exposes the same context shape the dashboard uses,
// with real KPI metrics so the Active Sessions card is wired like production.
jest.mock('@/app/admin/components/AdminDashboardProvider', () => {
  /* eslint-disable @typescript-eslint/no-require-imports */
  const React = require('react');
  const { buildKpiMetrics } = require('@/app/admin/components/utils');
  /* eslint-enable @typescript-eslint/no-require-imports */
  const Ctx = React.createContext(null);
  return {
    AdminDashboardProvider: ({ children }: { children: React.ReactNode }) => {
      const [sessionsModalOpen, setOpen] = React.useState(false);
      const openSessionsModal = () => setOpen(true);
      const value = {
        analytics: null,
        isLoading: false,
        errors: {},
        refetchAll: () => undefined,
        sessionsModalOpen,
        openSessionsModal,
        closeSessionsModal: () => setOpen(false),
        kpiMetrics: buildKpiMetrics(
          {
            total_registered_users: 10,
            active_learners_7d: 4,
            users_completed_all: 0,
            average_completion_rate: 50,
            total_capstone_submissions: 2,
          },
          3,
          openSessionsModal
        ),
      };
      return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
    },
    useAdminContext: () => {
      const v = React.useContext(Ctx);
      return v ?? { analytics: null };
    },
  };
});

// Stub heavy dashboard sections that are irrelevant here
jest.mock('@/app/admin/components/RegistrationAnalytics', () => ({ RegistrationAnalytics: () => null }));
jest.mock('@/app/admin/components/NeedsAttentionPanel', () => ({ NeedsAttentionPanel: () => null }));
jest.mock('@/app/admin/components/ActivitySection', () => ({ ActivitySection: () => null }));
jest.mock('@/app/admin/components/JourneyAnalyticsSection', () => ({ JourneyAnalyticsSection: () => null }));
jest.mock('@/app/admin/components/DangerZone', () => ({ DangerZone: () => null }));
jest.mock('@/app/admin/components/AdministrativeTools', () => ({ AdministrativeTools: () => null }));

const mockAuth = useAuth as jest.Mock;
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function announcements(failed: number) {
  return { data: { enabled: true, failed_count: failed, announcements: [] }, statusCode: 200 };
}

beforeEach(() => {
  jest.clearAllMocks();
  mockAuth.mockReturnValue({ isAdmin: true, isAuthenticated: true, isLoading: false });
});

describe('Broadcasts launcher card', () => {
  it('links to /admin/broadcasts and requests FAILED announcements', async () => {
    mockApi.getAnnouncements.mockResolvedValue(announcements(0) as never);
    render(<AdminDashboardPage />);
    expect(screen.getByRole('link', { name: 'Manage Broadcasts' })).toHaveAttribute('href', '/admin/broadcasts');
    expect(screen.getByRole('link', { name: 'Manage Videos' })).toBeInTheDocument();
    await waitFor(() => expect(mockApi.getAnnouncements).toHaveBeenCalledWith('FAILED'));
  });

  it('shows the failed badge when failed_count > 0', async () => {
    mockApi.getAnnouncements.mockResolvedValue(announcements(3) as never);
    render(<AdminDashboardPage />);
    expect(await screen.findByText('3 failed')).toBeInTheDocument();
  });

  it('hides the badge when failed_count is 0', async () => {
    mockApi.getAnnouncements.mockResolvedValue(announcements(0) as never);
    render(<AdminDashboardPage />);
    await waitFor(() => expect(mockApi.getAnnouncements).toHaveBeenCalled());
    expect(screen.queryByText(/failed$/)).not.toBeInTheDocument();
  });

  it('renders the card without a badge when the fetch fails', async () => {
    mockApi.getAnnouncements.mockResolvedValue({ error: 'boom', statusCode: 500 });
    render(<AdminDashboardPage />);
    await waitFor(() => expect(mockApi.getAnnouncements).toHaveBeenCalled());
    expect(screen.getByRole('link', { name: 'Manage Broadcasts' })).toBeInTheDocument();
    expect(screen.queryByText(/failed$/)).not.toBeInTheDocument();
  });

  it('renders the card without a badge when the fetch rejects', async () => {
    mockApi.getAnnouncements.mockRejectedValue(new Error('network'));
    render(<AdminDashboardPage />);
    await waitFor(() => expect(mockApi.getAnnouncements).toHaveBeenCalled());
    expect(screen.getByRole('link', { name: 'Manage Broadcasts' })).toBeInTheDocument();
    expect(screen.queryByText(/failed$/)).not.toBeInTheDocument();
  });
});

describe('Active Sessions KPI', () => {
  it('still opens the sessions modal', async () => {
    mockApi.getAnnouncements.mockResolvedValue(announcements(0) as never);
    render(<AdminDashboardPage />);
    expect(screen.queryByRole('dialog', { name: 'Active Sessions Modal' })).not.toBeInTheDocument();
    fireEvent.click(screen.getByText('Active Sessions'));
    expect(await screen.findByRole('dialog', { name: 'Active Sessions Modal' })).toBeInTheDocument();
  });
});

describe('navigation targets', () => {
  it('no targetSectionId points at a removed section', () => {
    const dir = path.join(__dirname, '../../app/admin/components');
    const source = ['NeedsAttentionPanel.tsx', 'AdminDashboardProvider.tsx', 'utils.ts']
      .map((f) => fs.readFileSync(path.join(dir, f), 'utf8'))
      .join('\n');
    const targets = Array.from(source.matchAll(/targetSectionId:\s*'([^']+)'/g)).map((m) => m[1]);
    expect(targets.length).toBeGreaterThan(0);
    for (const t of targets) {
      expect(['communications', 'system']).not.toContain(t);
    }
  });
});
