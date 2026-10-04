/**
 * Unit tests for lib/api.ts (ApiClient).
 *
 * The client builds requests through a single private `request` method, so
 * exercising a representative sample of verbs/endpoints covers the shared
 * success / error-body / network-failure / auth-header branches.
 */

// The singleton reads NEXT_PUBLIC_API_URL at module-load time, and next/jest
// may have already loaded env files. Load a fresh module instance with a known
// base URL via isolateModules so URL assertions are deterministic.
let apiClient: typeof import('@/lib/api').apiClient;

jest.isolateModules(() => {
  process.env.NEXT_PUBLIC_API_URL = 'https://api.test';
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  apiClient = require('@/lib/api').apiClient;
});

const mockFetch = jest.fn();
global.fetch = mockFetch;

function okJson(body: unknown, status = 200) {
  return Promise.resolve({
    ok: true,
    status,
    statusText: 'OK',
    json: () => Promise.resolve(body),
  });
}

function errJson(body: unknown, status = 400, statusText = 'Bad Request') {
  return Promise.resolve({
    ok: false,
    status,
    statusText,
    json: () => Promise.resolve(body),
  });
}

beforeEach(() => {
  mockFetch.mockReset();
  // Reset cookies between tests.
  Object.defineProperty(document, 'cookie', { writable: true, value: '' });
});

describe('request success path', () => {
  it('returns data and statusCode on a successful GET', async () => {
    mockFetch.mockReturnValueOnce(okJson({ authenticated: true, user_id: 'u1' }));
    const res = await apiClient.checkAuth();
    expect(res.data).toEqual({ authenticated: true, user_id: 'u1' });
    expect(res.statusCode).toBe(200);

    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toBe('https://api.test/me');
    expect(opts.method).toBe('GET');
    expect(opts.credentials).toBe('include');
    expect(opts.headers['Content-Type']).toBe('application/json');
  });

  it('serializes a JSON body on PUT', async () => {
    mockFetch.mockReturnValueOnce(okJson({ message: 'saved' }));
    const res = await apiClient.saveProgress('content-1', 'https://github.com/me/repo');
    expect(res.data).toEqual({ message: 'saved' });
    const [, opts] = mockFetch.mock.calls[0];
    expect(opts.method).toBe('PUT');
    expect(JSON.parse(opts.body)).toEqual({
      content_id: 'content-1',
      repo_url: 'https://github.com/me/repo',
    });
  });

  it('omits repo_url when not provided', async () => {
    mockFetch.mockReturnValueOnce(okJson({ message: 'saved' }));
    await apiClient.saveProgress('content-1');
    const [, opts] = mockFetch.mock.calls[0];
    expect(JSON.parse(opts.body)).toEqual({ content_id: 'content-1' });
  });

  it('issues a POST with an empty object body on logout', async () => {
    mockFetch.mockReturnValueOnce(okJson({ message: 'bye' }));
    await apiClient.logout();
    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toBe('https://api.test/logout');
    expect(opts.method).toBe('POST');
  });

  it('issues a DELETE on resetProgress', async () => {
    mockFetch.mockReturnValueOnce(okJson({ message: 'reset', user_id: 'u1' }));
    const res = await apiClient.resetProgress();
    expect(res.data?.message).toBe('reset');
    expect(mockFetch.mock.calls[0][1].method).toBe('DELETE');
  });

  it('url-encodes path parameters', async () => {
    mockFetch.mockReturnValueOnce(okJson({ contributor_role: null }));
    await apiClient.getContributorRole('user/with space');
    expect(mockFetch.mock.calls[0][0]).toBe(
      'https://api.test/admin/users/user%2Fwith%20space/contributor-role',
    );
  });

  it('builds query strings for paginated list endpoints', async () => {
    mockFetch.mockReturnValueOnce(okJson({ users: [], total_count: 0 }));
    await apiClient.listUsers(2, 25, 'ada', 'ada@example.com', 'admin');
    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain('page=2');
    expect(url).toContain('page_size=25');
    expect(url).toContain('search=ada');
    expect(url).toContain('email=ada%40example.com');
    expect(url).toContain('role=admin');
  });
});

describe('auth header from cookie', () => {
  it('adds a Bearer Authorization header when the session cookie is present', async () => {
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: 'dsb_session=abc123; other=x',
    });
    mockFetch.mockReturnValueOnce(okJson({ authenticated: true }));
    await apiClient.checkAuth();
    expect(mockFetch.mock.calls[0][1].headers['Authorization']).toBe('Bearer abc123');
  });

  it('omits Authorization when no session cookie exists', async () => {
    mockFetch.mockReturnValueOnce(okJson({ authenticated: false }));
    await apiClient.checkAuth();
    expect(mockFetch.mock.calls[0][1].headers['Authorization']).toBeUndefined();
  });
});

describe('error handling', () => {
  it('surfaces a backend error detail with the status code', async () => {
    mockFetch.mockReturnValueOnce(errJson({ detail: 'nope' }, 403, 'Forbidden'));
    const res = await apiClient.getStats();
    expect(res.error).toBe('nope');
    expect(res.statusCode).toBe(403);
  });

  it('falls back to an HTTP status message when the error body has no message', async () => {
    mockFetch.mockReturnValueOnce(errJson({}, 500, 'Server Error'));
    const res = await apiClient.getStats();
    expect(res.error).toMatch(/HTTP 500/);
  });

  it('returns a network error message when fetch throws', async () => {
    mockFetch.mockRejectedValueOnce(new Error('offline'));
    const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
    const res = await apiClient.getStats();
    expect(res.error).toBe('offline');
    spy.mockRestore();
  });
});

describe('OAuth start URLs', () => {
  it('builds provider start URLs from the base URL', () => {
    expect(apiClient.getAuthStartUrl()).toBe('https://api.test/auth/github/start');
    expect(apiClient.getGitLabAuthStartUrl()).toBe('https://api.test/auth/gitlab/start');
    expect(apiClient.getBitbucketAuthStartUrl()).toBe('https://api.test/auth/bitbucket/start');
  });
});

describe('CSV export (blob download)', () => {
  let clickSpy: jest.Mock;
  beforeEach(() => {
    clickSpy = jest.fn();
    // jsdom lacks URL.createObjectURL / revokeObjectURL
    window.URL.createObjectURL = jest.fn(() => 'blob:mock');
    window.URL.revokeObjectURL = jest.fn();
    jest.spyOn(document, 'createElement').mockReturnValue({
      href: '',
      download: '',
      click: clickSpy,
    } as unknown as HTMLAnchorElement);
    jest.spyOn(document.body, 'appendChild').mockImplementation((n) => n);
    jest.spyOn(document.body, 'removeChild').mockImplementation((n) => n);
  });

  it('downloads a users export CSV on success', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(new Blob(['a,b'])),
    });
    await apiClient.exportUsers();
    expect(clickSpy).toHaveBeenCalledTimes(1);
    expect(window.URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock');
  });

  it('throws when the export request fails', async () => {
    mockFetch.mockResolvedValueOnce({ ok: false });
    const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
    await expect(apiClient.exportCapstoneSubmissions()).rejects.toThrow('Export failed');
    spy.mockRestore();
  });
});

describe('endpoint URL + method coverage', () => {
  beforeEach(() => {
    // Every call resolves with a trivial OK body.
    mockFetch.mockReturnValue(okJson({}));
  });

  // [callFn, expectedMethod, expectedUrlFragment]
  const cases: Array<[() => Promise<unknown>, string, string]> = [
    [() => apiClient.getProgress(), 'GET', '/progress'],
    [() => apiClient.getCapstoneSubmission('c1'), 'GET', '/progress/capstone/c1'],
    [() => apiClient.getRecentActivities(), 'GET', '/progress/recent'],
    [() => apiClient.getBadges(), 'GET', '/progress/badges'],
    [() => apiClient.saveLastActiveLesson('p1', 'slug'), 'PUT', '/progress/last-active'],
    [() => apiClient.getLastActiveLesson(), 'GET', '/progress/last-active'],
    [() => apiClient.getAnalytics(), 'GET', '/admin/analytics'],
    [() => apiClient.getCapstoneSubmissions(2, 10), 'GET', '/admin/submissions?page=2&page_size=10'],
    [() => apiClient.getCertificatePreview('cred 1'), 'GET', '/admin/certifications/credentials/cred%201/preview'],
    [() => apiClient.getRegistryStatus(), 'GET', '/admin/registry-status'],
    [() => apiClient.getModuleHealth(), 'GET', '/admin/module-health'],
    [() => apiClient.getWalkthroughStatistics(), 'GET', '/admin/walkthrough-statistics'],
    [() => apiClient.getActiveSessions(), 'GET', '/admin/sessions'],
    [() => apiClient.searchUsers('ada'), 'GET', '/admin/users/search?q=ada'],
    [() => apiClient.getAdminUserProfile('u1'), 'GET', '/admin/users/u1/profile'],
    [() => apiClient.setContributorRole('u1', 'author' as never, 'note'), 'PUT', '/admin/users/u1/contributor-role'],
    [() => apiClient.deleteContributorRole('u1'), 'DELETE', '/admin/users/u1/contributor-role'],
    [() => apiClient.getWalkthroughAccessTiers(), 'GET', '/api/walkthroughs/access-tiers'],
    [() => apiClient.getAdminWalkthroughAccessTiers(), 'GET', '/admin/walkthroughs/access-tiers'],
    [() => apiClient.setWalkthroughAccessTier('w1', 'BUILDER'), 'PUT', '/admin/walkthroughs/w1/access-tier'],
    [() => apiClient.deleteWalkthroughAccessTier('w1'), 'DELETE', '/admin/walkthroughs/w1/access-tier'],
    [() => apiClient.getUnreadBroadcasts(), 'GET', '/api/broadcasts/unread'],
    [() => apiClient.dismissBroadcast('b1'), 'POST', '/api/broadcasts/b1/dismiss'],
    [() => apiClient.dismissAllBroadcasts(), 'POST', '/api/broadcasts/dismiss-all'],
    [() => apiClient.createBroadcast('t', 'm', 'l'), 'POST', '/admin/broadcasts'],
    [() => apiClient.getAdminBroadcasts(), 'GET', '/admin/broadcasts'],
    [() => apiClient.deleteBroadcast('b1'), 'DELETE', '/admin/broadcasts/b1'],
    [() => apiClient.getUserProfile(), 'GET', '/user/profile'],
    [() => apiClient.getWalkthroughProgress('w1'), 'GET', '/api/walkthroughs/w1/progress'],
    [() => apiClient.updateWalkthroughProgress('w1', 'completed'), 'POST', '/api/walkthroughs/w1/progress'],
    [() => apiClient.getNotifications(), 'GET', '/api/notifications'],
    [() => apiClient.deleteNotification('n1'), 'DELETE', '/api/notifications/n1'],
  ];

  it.each(cases)('calls the right method and URL [%#]', async (call, method, fragment) => {
    mockFetch.mockClear();
    await call();
    const [url, opts] = mockFetch.mock.calls[0];
    expect(opts.method).toBe(method);
    expect(url).toContain(fragment);
  });
});
