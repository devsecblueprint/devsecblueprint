/**
 * Unit tests for JourneyAnalyticsSection.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { JourneyAnalyticsSection } from '@/app/admin/components/JourneyAnalyticsSection';

jest.mock('@/lib/api', () => ({ apiClient: { get: jest.fn() } }));
jest.mock('@/app/admin/components/KpiCard', () => ({
  KpiCard: ({ label, value }: { label: string; value: unknown }) => (
    <div data-testid="kpi">{label}: {String(value)}</div>
  ),
}));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

const DATA = {
  totals: {
    journeys_started: 50,
    journeys_completed: 20,
    completion_rate: 40,
    average_duration_days: 10,
    seven_day_active_rate: 25,
    active_7d_count: 12,
  },
  by_tier: {
    FREE: { journeys_started: 30, journeys_completed: 10, active_users: 8, completion_rate: 33 },
    BUILDER: { journeys_started: 20, journeys_completed: 10, active_users: 4, completion_rate: 50 },
  },
  phase_distribution: {},
  phase_distribution_named: [
    { phase: 1, name: 'Getting Started', count: 10 },
    { phase: 2, name: 'Building', count: 5 },
  ],
  phase_completion_funnel: [],
  task_completion_rates: [
    { task_id: 'task-b', phase: 2, completion_rate: 80 },
    { task_id: 'task-a', phase: 1, completion_rate: 60 },
  ],
  key_rates: { discord_connection_rate: 50, prerequisites_completion_rate: 70 },
  timeline_30d: { starts: [{ date: '2026-01-01', count: 3 }], completions: [{ date: '2026-01-01', count: 1 }] },
};

beforeEach(() => jest.clearAllMocks());

it('shows a loading skeleton initially', () => {
  mockApi.get.mockReturnValue(new Promise(() => {})); // never resolves
  render(<JourneyAnalyticsSection />);
  expect(screen.getByLabelText('Onboarding Guide Analytics')).toHaveAttribute('aria-busy', 'true');
});

it('shows an error state with retry', async () => {
  mockApi.get.mockResolvedValue({ error: 'analytics failed', statusCode: 500 });
  render(<JourneyAnalyticsSection />);
  expect(await screen.findByText('analytics failed')).toBeInTheDocument();
  mockApi.get.mockResolvedValue({ data: DATA as never, statusCode: 200 });
  fireEvent.click(screen.getByRole('button', { name: /retry/i }));
  await waitFor(() => expect(screen.getByRole('button', { name: /Onboarding Guide Analytics/i })).toBeInTheDocument());
});

it('renders collapsed by default, then expands to show analytics', async () => {
  mockApi.get.mockResolvedValue({ data: DATA as never, statusCode: 200 });
  render(<JourneyAnalyticsSection />);
  const toggle = await screen.findByRole('button', { name: /Onboarding Guide Analytics/i });
  // Collapsed: KPI cards not shown yet
  expect(screen.queryByText(/Journeys Started/)).not.toBeInTheDocument();

  fireEvent.click(toggle);
  expect(screen.getByText(/Journeys Started: 50/)).toBeInTheDocument();
  expect(screen.getByText('Where Users Are Now')).toBeInTheDocument();
  expect(screen.getByText('Getting Started')).toBeInTheDocument();
});

it('sorts the task completion table when a header is clicked', async () => {
  mockApi.get.mockResolvedValue({ data: DATA as never, statusCode: 200 });
  render(<JourneyAnalyticsSection />);
  fireEvent.click(await screen.findByRole('button', { name: /Onboarding Guide Analytics/i }));

  // Default sort is by phase asc: task-a (phase 1) before task-b (phase 2)
  let rows = screen.getAllByRole('row');
  // rows[0] is the header; first data row should contain task-a
  expect(rows[1]).toHaveTextContent('task-a');

  // Click the Completion Rate column header to sort asc (60 then 80 => task-a first)
  const completionHeader = screen.getByRole('columnheader', { name: /Completion Rate/ });
  fireEvent.click(completionHeader);
  rows = screen.getAllByRole('row');
  expect(rows[1]).toHaveTextContent('task-a');
});
