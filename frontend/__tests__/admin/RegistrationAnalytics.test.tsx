/**
 * Unit tests for RegistrationAnalytics (SVG chart + states).
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { useAdminContext } from '@/app/admin/components/AdminDashboardProvider';
import { RegistrationAnalytics } from '@/app/admin/components/RegistrationAnalytics';

jest.mock('@/app/admin/components/AdminDashboardProvider', () => ({
  useAdminContext: jest.fn(),
}));
const mockCtx = useAdminContext as jest.Mock;

function ctx(overrides: Record<string, unknown> = {}) {
  return {
    analytics: null,
    isLoading: false,
    errors: {},
    refetchAnalytics: jest.fn(),
    ...overrides,
  };
}

beforeEach(() => jest.clearAllMocks());

it('renders the chart when timeline data is present', () => {
  const today = new Date().toISOString().split('T')[0];
  mockCtx.mockReturnValue(
    ctx({ analytics: { registration_timeline: [{ date: today, count: 5 }] } }),
  );
  render(<RegistrationAnalytics />);
  expect(screen.getByText('New User Registrations')).toBeInTheDocument();
  expect(screen.getByRole('img', { name: /new user registrations over time/i })).toBeInTheDocument();
});

it('shows the empty state when there is no data in range', () => {
  mockCtx.mockReturnValue(ctx({ analytics: { registration_timeline: [] } }));
  render(<RegistrationAnalytics />);
  expect(screen.getByText(/No registration data available/i)).toBeInTheDocument();
});

it('shows an error state with retry', () => {
  const refetchAnalytics = jest.fn();
  mockCtx.mockReturnValue(ctx({ errors: { analytics: 'API down' }, refetchAnalytics }));
  render(<RegistrationAnalytics />);
  expect(screen.getByText('API down')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /retry/i }));
  expect(refetchAnalytics).toHaveBeenCalled();
});

it('validates the date range and shows an error for an inverted range', () => {
  mockCtx.mockReturnValue(ctx({ analytics: { registration_timeline: [] } }));
  render(<RegistrationAnalytics />);
  // Set start date far after end date
  fireEvent.change(screen.getByLabelText('Start date'), { target: { value: '2030-01-01' } });
  expect(screen.getByRole('alert')).toHaveTextContent(/before end date/i);
});
