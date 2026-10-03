/**
 * Unit tests for AdminResetButton.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useAuth } from '@/lib/hooks/useAuth';
import { apiClient } from '@/lib/api';
import { AdminResetButton } from '@/components/features/AdminResetButton';

jest.mock('@/lib/hooks/useAuth', () => ({ useAuth: jest.fn() }));
jest.mock('@/lib/api', () => ({ apiClient: { resetProgress: jest.fn(), logout: jest.fn() } }));
const mockUseAuth = useAuth as jest.Mock;
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

let originalLocation: Location;
beforeAll(() => { originalLocation = window.location; });
afterAll(() => {
  // @ts-expect-error restore
  window.location = originalLocation;
});

beforeEach(() => {
  jest.clearAllMocks();
  // @ts-expect-error override
  delete window.location;
  // @ts-expect-error stub
  window.location = { href: '' };
});

it('renders nothing for non-admin users', () => {
  mockUseAuth.mockReturnValue({ username: 'random-user' });
  const { container } = render(<AdminResetButton />);
  expect(container).toBeEmptyDOMElement();
});

it('renders admin controls for an allow-listed user', () => {
  mockUseAuth.mockReturnValue({ username: 'damienjburks' });
  render(<AdminResetButton />);
  expect(screen.getByText('Admin Controls')).toBeInTheDocument();
});

it('shows the confirmation panel when reset is clicked', () => {
  mockUseAuth.mockReturnValue({ username: 'damienjburks' });
  render(<AdminResetButton />);
  fireEvent.click(screen.getByRole('button', { name: /reset all progress/i }));
  expect(screen.getByText('Confirm Progress Reset')).toBeInTheDocument();
});

it('resets, logs out, and redirects on confirm', async () => {
  mockUseAuth.mockReturnValue({ username: 'damienjburks' });
  mockApi.resetProgress.mockResolvedValue({ data: { message: 'ok', user_id: 'u1' }, statusCode: 200 });
  mockApi.logout.mockResolvedValue({ data: { message: 'bye' }, statusCode: 200 });

  render(<AdminResetButton />);
  fireEvent.click(screen.getByRole('button', { name: /reset all progress/i }));
  fireEvent.click(screen.getByRole('button', { name: /yes, reset all progress/i }));

  await waitFor(() => expect(mockApi.resetProgress).toHaveBeenCalled());
  await waitFor(() => expect(mockApi.logout).toHaveBeenCalled());
  expect(window.location.href).toBe('/');
});

it('shows an error when reset fails', async () => {
  mockUseAuth.mockReturnValue({ username: 'damienjburks' });
  mockApi.resetProgress.mockResolvedValue({ error: 'reset failed', statusCode: 500 });

  render(<AdminResetButton />);
  fireEvent.click(screen.getByRole('button', { name: /reset all progress/i }));
  fireEvent.click(screen.getByRole('button', { name: /yes, reset all progress/i }));
  expect(await screen.findByText(/reset failed/i)).toBeInTheDocument();
  expect(mockApi.logout).not.toHaveBeenCalled();
});

it('cancels the confirmation', () => {
  mockUseAuth.mockReturnValue({ username: 'damienjburks' });
  render(<AdminResetButton />);
  fireEvent.click(screen.getByRole('button', { name: /reset all progress/i }));
  fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
  expect(screen.getByText('Admin Controls')).toBeInTheDocument();
});
