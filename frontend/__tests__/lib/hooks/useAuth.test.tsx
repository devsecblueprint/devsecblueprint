/**
 * Unit tests for the AuthProvider / useAuth context hook.
 */
import { render, screen, waitFor, act, renderHook } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { AuthProvider, useAuth } from '@/lib/hooks/useAuth';

jest.mock('@/lib/api', () => ({ apiClient: { checkAuth: jest.fn(), logout: jest.fn(), post: jest.fn() } }));
// Avoid pulling the real modal into these tests.
jest.mock('@/components/SessionExpiryModal', () => ({ SessionExpiryModal: () => null }));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function Consumer() {
  const { isAuthenticated, isLoading, userId, isAdmin, providerUsername } = useAuth();
  return (
    <div>
      <span data-testid="loading">{String(isLoading)}</span>
      <span data-testid="auth">{String(isAuthenticated)}</span>
      <span data-testid="user">{userId ?? 'none'}</span>
      <span data-testid="admin">{String(isAdmin)}</span>
      <span data-testid="provider-username">{providerUsername ?? 'none'}</span>
    </div>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  jest.spyOn(console, 'log').mockImplementation(() => {});
  Object.defineProperty(document, 'cookie', { writable: true, value: '' });
});

it('throws if useAuth is used outside the provider', () => {
  const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
  expect(() => renderHook(() => useAuth())).toThrow(/within an AuthProvider/);
  spy.mockRestore();
});

it('exposes authenticated state after a successful check', async () => {
  mockApi.checkAuth.mockResolvedValue({
    data: {
      authenticated: true,
      user_id: 'u1',
      is_admin: true,
      provider: 'github',
      github_username: 'ada-gh',
    } as never,
    statusCode: 200,
  });

  render(
    <AuthProvider>
      <Consumer />
    </AuthProvider>,
  );

  await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));
  expect(screen.getByTestId('auth').textContent).toBe('true');
  expect(screen.getByTestId('user').textContent).toBe('u1');
  expect(screen.getByTestId('admin').textContent).toBe('true');
  expect(screen.getByTestId('provider-username').textContent).toBe('ada-gh');
});

it('exposes unauthenticated state when the check fails', async () => {
  mockApi.checkAuth.mockResolvedValue({ data: { authenticated: false } as never, statusCode: 200 });

  render(
    <AuthProvider>
      <Consumer />
    </AuthProvider>,
  );

  await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));
  expect(screen.getByTestId('auth').textContent).toBe('false');
  expect(screen.getByTestId('user').textContent).toBe('none');
});

it('derives the provider username based on the provider', async () => {
  mockApi.checkAuth.mockResolvedValue({
    data: {
      authenticated: true,
      user_id: 'u1',
      provider: 'gitlab',
      gitlab_username: 'ada-gl',
      github_username: 'ada-gh',
    } as never,
    statusCode: 200,
  });

  render(
    <AuthProvider>
      <Consumer />
    </AuthProvider>,
  );
  await waitFor(() => expect(screen.getByTestId('provider-username').textContent).toBe('ada-gl'));
});

it('logout clears state and redirects home', async () => {
  mockApi.checkAuth.mockResolvedValue({
    data: { authenticated: true, user_id: 'u1' } as never,
    statusCode: 200,
  });
  mockApi.logout.mockResolvedValue({ data: { message: 'ok' }, statusCode: 200 });

  // jsdom: make location.href assignable
  const originalLocation = window.location;
  // @ts-expect-error override for test
  delete window.location;
  // @ts-expect-error minimal stub
  window.location = { href: '', hostname: 'localhost' };

  let auth: ReturnType<typeof useAuth>;
  function Grab() {
    auth = useAuth();
    return null;
  }
  render(
    <AuthProvider>
      <Grab />
    </AuthProvider>,
  );
  await waitFor(() => expect(auth.isAuthenticated).toBe(true));

  await act(async () => {
    await auth.logout();
  });

  expect(mockApi.logout).toHaveBeenCalled();
  expect(window.location.href).toBe('/');

  // restore
  // @ts-expect-error restore
  window.location = originalLocation;
});
