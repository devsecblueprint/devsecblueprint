/**
 * Unit tests for AdminDashboardProvider + useAdminContext.
 */
import { render, screen, waitFor, act, renderHook } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { AdminDashboardProvider, useAdminContext } from '@/app/admin/components/AdminDashboardProvider';

jest.mock('@/lib/api', () => ({
  apiClient: {
    getAnalytics: jest.fn(),
    getActiveSessions: jest.fn(),
    getCapstoneSubmissions: jest.fn(),
    getModuleHealth: jest.fn(),
    getRegistryStatus: jest.fn(),
  },
}));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function Consumer() {
  const { isLoading, errors, kpiMetrics, attentionCounts, sessionsModalOpen, openSessionsModal } = useAdminContext();
  return (
    <div>
      <span data-testid="loading">{String(isLoading)}</span>
      <span data-testid="kpi-count">{kpiMetrics.length}</span>
      <span data-testid="pending-caps">{attentionCounts.pendingCapstones}</span>
      <span data-testid="analytics-error">{errors.analytics ?? 'none'}</span>
      <span data-testid="modal">{String(sessionsModalOpen)}</span>
      <button onClick={openSessionsModal}>open-modal</button>
    </div>
  );
}

function okAll() {
  mockApi.getAnalytics.mockResolvedValue({
    data: {
      total_registered_users: 100,
      active_learners_7d: 10,
      users_completed_all: 2,
      average_completion_rate: 40,
      total_capstone_submissions: 5,
    } as never,
    statusCode: 200,
  });
  mockApi.getActiveSessions.mockResolvedValue({ data: { sessions: [], total_active: 3 }, statusCode: 200 });
  mockApi.getCapstoneSubmissions.mockResolvedValue({
    data: { submissions: [{ status: 'pending' }], total_count: 1, page: 1, page_size: 50, total_pages: 1 } as never,
    statusCode: 200,
  });
  mockApi.getModuleHealth.mockResolvedValue({ data: { validation_errors: [] } as never, statusCode: 200 });
  mockApi.getRegistryStatus.mockResolvedValue({ data: { status: 'healthy' } as never, statusCode: 200 });
}

beforeEach(() => jest.clearAllMocks());

it('throws when useAdminContext is used outside the provider', () => {
  const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
  expect(() => renderHook(() => useAdminContext())).toThrow(/within an AdminDashboardProvider/);
  spy.mockRestore();
});

it('loads all dashboard data and derives KPIs and attention counts', async () => {
  okAll();
  render(
    <AdminDashboardProvider>
      <Consumer />
    </AdminDashboardProvider>,
  );
  await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));
  expect(Number(screen.getByTestId('kpi-count').textContent)).toBeGreaterThan(0);
  expect(screen.getByTestId('pending-caps').textContent).toBe('1');
  expect(screen.getByTestId('analytics-error').textContent).toBe('none');
});

it('records an analytics error when that endpoint fails', async () => {
  okAll();
  mockApi.getAnalytics.mockResolvedValue({ error: 'analytics down', statusCode: 500 });
  render(
    <AdminDashboardProvider>
      <Consumer />
    </AdminDashboardProvider>,
  );
  await waitFor(() => expect(screen.getByTestId('analytics-error').textContent).toBe('analytics down'));
});

it('handles a rejected request (allSettled rejection)', async () => {
  okAll();
  mockApi.getModuleHealth.mockRejectedValue(new Error('network'));
  render(
    <AdminDashboardProvider>
      <Consumer />
    </AdminDashboardProvider>,
  );
  // Should still finish loading without throwing
  await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));
});

it('opens the sessions modal via the context action', async () => {
  okAll();
  render(
    <AdminDashboardProvider>
      <Consumer />
    </AdminDashboardProvider>,
  );
  await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));
  act(() => screen.getByText('open-modal').click());
  expect(screen.getByTestId('modal').textContent).toBe('true');
});
