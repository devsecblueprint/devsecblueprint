/**
 * Unit tests for the admin DangerZone (type-to-confirm destructive action).
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { DangerZone } from '@/app/admin/components/DangerZone';

jest.mock('@/lib/api', () => ({ apiClient: { resetProgress: jest.fn(), logout: jest.fn() } }));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

const CONFIRM_PHRASE = 'RESET ALL PROGRESS';

let originalLocation: Location;
beforeAll(() => {
  originalLocation = window.location;
});
afterAll(() => {
  // @ts-expect-error restore
  window.location = originalLocation;
});

beforeEach(() => {
  jest.clearAllMocks();
  // @ts-expect-error override for test
  delete window.location;
  // @ts-expect-error minimal stub
  window.location = { href: '' };
});

it('reveals the confirmation panel when the action is triggered', () => {
  render(<DangerZone />);
  // The action button is labeled with the action name; there is one before expansion.
  fireEvent.click(screen.getByRole('button', { name: 'Reset All Progress' }));
  expect(screen.getByText(/This action is irreversible/i)).toBeInTheDocument();
  expect(screen.getByLabelText(new RegExp(`Type ${CONFIRM_PHRASE} to confirm`))).toBeInTheDocument();
});

it('keeps Confirm disabled until the exact phrase is typed', () => {
  render(<DangerZone />);
  fireEvent.click(screen.getByRole('button', { name: 'Reset All Progress' }));
  const confirm = screen.getByRole('button', { name: /^confirm$/i });
  expect(confirm).toBeDisabled();

  fireEvent.change(screen.getByLabelText(new RegExp(`Type ${CONFIRM_PHRASE} to confirm`)), {
    target: { value: 'wrong' },
  });
  expect(confirm).toBeDisabled();

  fireEvent.change(screen.getByLabelText(new RegExp(`Type ${CONFIRM_PHRASE} to confirm`)), {
    target: { value: CONFIRM_PHRASE },
  });
  expect(confirm).toBeEnabled();
});

it('executes the reset and redirects on success', async () => {
  mockApi.resetProgress.mockResolvedValue({ data: { message: 'ok', user_id: 'u1' }, statusCode: 200 });
  mockApi.logout.mockResolvedValue({ data: { message: 'bye' }, statusCode: 200 });

  render(<DangerZone />);
  fireEvent.click(screen.getByRole('button', { name: 'Reset All Progress' }));
  fireEvent.change(screen.getByLabelText(new RegExp(`Type ${CONFIRM_PHRASE} to confirm`)), {
    target: { value: CONFIRM_PHRASE },
  });
  fireEvent.click(screen.getByRole('button', { name: /^confirm$/i }));

  await waitFor(() => expect(mockApi.resetProgress).toHaveBeenCalled());
  await waitFor(() => expect(mockApi.logout).toHaveBeenCalled());
  expect(window.location.href).toBe('/');
});

it('shows an error when reset fails', async () => {
  mockApi.resetProgress.mockResolvedValue({ error: 'cannot reset', statusCode: 500 });
  render(<DangerZone />);
  fireEvent.click(screen.getByRole('button', { name: 'Reset All Progress' }));
  fireEvent.change(screen.getByLabelText(new RegExp(`Type ${CONFIRM_PHRASE} to confirm`)), {
    target: { value: CONFIRM_PHRASE },
  });
  fireEvent.click(screen.getByRole('button', { name: /^confirm$/i }));
  expect(await screen.findByRole('alert')).toHaveTextContent('cannot reset');
  expect(mockApi.logout).not.toHaveBeenCalled();
});

it('cancels the confirmation panel', () => {
  render(<DangerZone />);
  fireEvent.click(screen.getByRole('button', { name: 'Reset All Progress' }));
  fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
  expect(screen.queryByText(/This action is irreversible/i)).not.toBeInTheDocument();
});
