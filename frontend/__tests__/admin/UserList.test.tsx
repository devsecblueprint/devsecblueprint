/**
 * Unit tests for the admin UserList component.
 */
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { UserList } from '@/components/admin/UserList';

jest.mock('@/lib/api', () => ({ apiClient: { listUsers: jest.fn() } }));
jest.mock('@/components/admin/UserProfileModal', () => ({
  UserProfileModal: ({ userId }: { userId: string }) => <div data-testid="profile-modal">{userId}</div>,
}));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function user(id: string, overrides: Record<string, unknown> = {}) {
  return {
    user_id: id,
    username: `user-${id}`,
    github_username: `gh-${id}`,
    gitlab_username: '',
    provider: 'github',
    avatar_url: '',
    registered_at: '2026-01-01T00:00:00Z',
    last_login: '2026-01-02T00:00:00Z',
    email: `${id}@example.com`,
    membership_tier: 'FREE',
    certifications_count: 0,
    ...overrides,
  };
}

function page(users: unknown[], overrides: Record<string, unknown> = {}) {
  return {
    data: { users, total_count: users.length, page: 1, page_size: 20, total_pages: 1, ...overrides },
    statusCode: 200,
  };
}

beforeEach(() => jest.clearAllMocks());

it('renders a list of users after loading', async () => {
  mockApi.listUsers.mockResolvedValue(page([user('1'), user('2')]));
  render(<UserList />);
  // Desktop + mobile views both render in jsdom, so each name appears twice.
  expect(await screen.findAllByText('user-1')).not.toHaveLength(0);
  expect(screen.getAllByText('user-2').length).toBeGreaterThan(0);
});

it('shows the empty state when there are no users', async () => {
  mockApi.listUsers.mockResolvedValue(page([]));
  render(<UserList />);
  expect(await screen.findByText('No users found')).toBeInTheDocument();
});

it('shows an error state with retry', async () => {
  mockApi.listUsers.mockResolvedValue({ error: 'server down', statusCode: 500 });
  render(<UserList />);
  expect(await screen.findByText('Failed to Load Users')).toBeInTheDocument();
  expect(screen.getByText('server down')).toBeInTheDocument();

  // Retry triggers another fetch
  mockApi.listUsers.mockResolvedValue(page([user('1')]));
  fireEvent.click(screen.getByRole('button', { name: /try again/i }));
  expect(await screen.findAllByText('user-1')).not.toHaveLength(0);
});

it('debounces search input before fetching', async () => {
  jest.useFakeTimers();
  mockApi.listUsers.mockResolvedValue(page([user('1')]));
  render(<UserList />);
  // flush initial fetch
  await act(async () => { await Promise.resolve(); });

  const search = screen.getByLabelText('Search users');
  fireEvent.change(search, { target: { value: 'ada' } });

  // Not called again until debounce elapses
  const callsBefore = mockApi.listUsers.mock.calls.length;
  act(() => { jest.advanceTimersByTime(300); });
  await waitFor(() =>
    expect(mockApi.listUsers.mock.calls.length).toBeGreaterThan(callsBefore),
  );
  const lastCall = mockApi.listUsers.mock.calls.at(-1)!;
  expect(lastCall).toContain('ada');
  jest.useRealTimers();
});

it('opens the profile modal when a user row is clicked', async () => {
  mockApi.listUsers.mockResolvedValue(page([user('1')]));
  render(<UserList />);
  const rows = await screen.findAllByRole('button', { name: /view profile for user-1/i });
  fireEvent.click(rows[0]);
  expect(screen.getByTestId('profile-modal')).toHaveTextContent('1');
});

it('disables pagination at the single-page boundary', async () => {
  mockApi.listUsers.mockResolvedValue(page([user('1')], { total_pages: 1 }));
  render(<UserList />);
  await screen.findAllByText('user-1');
  expect(screen.getByRole('button', { name: /previous/i })).toBeDisabled();
  expect(screen.getByRole('button', { name: /next/i })).toBeDisabled();
});

it('advances to the next page', async () => {
  mockApi.listUsers.mockResolvedValue(page([user('1')], { total_pages: 3 }));
  render(<UserList />);
  await screen.findAllByText('user-1');
  fireEvent.click(screen.getByRole('button', { name: /next/i }));
  await waitFor(() => {
    const lastCall = mockApi.listUsers.mock.calls.at(-1)!;
    expect(lastCall[0]).toBe(2); // page arg
  });
});
