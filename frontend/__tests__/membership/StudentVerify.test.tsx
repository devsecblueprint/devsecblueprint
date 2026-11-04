/**
 * Student verification UI tests (Task 20.2)
 *
 * Covers the two verification pages:
 *  - Submit page  (app/pricing/verify/page.tsx): academic-email submission,
 *    the 202 "check your email" state, the friendly error messages for each
 *    backend status code (400/422/429/502/503), and the login redirect for
 *    unauthenticated visitors.
 *  - Confirm page (app/verify/confirm/page.tsx): reads the `token` query param,
 *    POSTs it, shows the success state + "Subscribe as Student" CTA on 200,
 *    shows an error + retry link on 400, and shows an immediate error when the
 *    token is missing.
 *
 * Requirements: 4.2, 4.4
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { useAuth } from '@/lib/hooks/useAuth';
import { apiClient } from '@/lib/api';

// --- Mocks -----------------------------------------------------------------

// next/navigation: router.push is asserted for the login redirect; a mutable
// URLSearchParams drives the confirm page's token lookup.
const mockPush = jest.fn();
let mockSearchParams = new URLSearchParams();

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
  usePathname: () => '/pricing/verify',
  useSearchParams: () => mockSearchParams,
}));

jest.mock('@/lib/hooks/useAuth', () => ({ useAuth: jest.fn() }));
jest.mock('@/lib/api', () => ({ apiClient: { post: jest.fn(), get: jest.fn() } }));

// Layout chrome pulls in auth context / theme providers that are irrelevant to
// these tests. Stub them out so the pages can render in isolation.
jest.mock('@/components/layout/NavbarWithAuth', () => ({
  NavbarWithAuth: () => <nav data-testid="navbar" />,
}));
jest.mock('@/components/layout/Footer', () => ({
  Footer: () => <footer data-testid="footer" />,
}));

// next/link renders a plain anchor so we can assert hrefs.
jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ href, children, ...rest }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

const mockUseAuth = useAuth as jest.Mock;
const mockApi = apiClient as unknown as { post: jest.Mock; get: jest.Mock };

// Imported after the mocks are registered.
import StudentVerifyPage from '@/app/pricing/verify/page';
import StudentVerifyConfirmPage from '@/app/verify/confirm/page';

beforeEach(() => {
  jest.clearAllMocks();
  mockSearchParams = new URLSearchParams();
});

// ===========================================================================
// Submit page — app/pricing/verify/page.tsx
// ===========================================================================

describe('StudentVerifyPage (submit)', () => {
  const authed = { isAuthenticated: true, isLoading: false };

  it('posts { academic_email } to the submit endpoint and shows the check-your-email state on 202', async () => {
    const user = userEvent.setup();
    mockUseAuth.mockReturnValue(authed);
    mockApi.post.mockResolvedValue({ statusCode: 202 });

    render(<StudentVerifyPage />);

    const email = 'student@university.edu';
    await user.type(screen.getByLabelText(/academic email/i), email);
    await user.click(screen.getByRole('button', { name: /send verification email/i }));

    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalledWith('/api/verification/student/submit', {
        academic_email: email,
      });
    });

    // 202 -> "check your email" success state.
    expect(await screen.findByText(/check your email/i)).toBeInTheDocument();
    expect(screen.getByText(email)).toBeInTheDocument();
  });

  it.each([
    [400, /valid email address/i],
    [422, /academic address/i],
    [429, /too many attempts/i],
    [502, /couldn.t send the verification email/i],
    [503, /temporarily unavailable/i],
  ])('shows the friendly %s error message', async (statusCode, pattern) => {
    const user = userEvent.setup();
    mockUseAuth.mockReturnValue(authed);
    mockApi.post.mockResolvedValue({ statusCode });

    render(<StudentVerifyPage />);

    await user.type(screen.getByLabelText(/academic email/i), 'someone@example.com');
    await user.click(screen.getByRole('button', { name: /send verification email/i }));

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(pattern);
    // The error state keeps the form visible rather than switching to success.
    expect(screen.queryByText(/check your email/i)).not.toBeInTheDocument();
  });

  it('redirects unauthenticated visitors to login with a returnTo of /pricing/verify', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false, isLoading: false });

    render(<StudentVerifyPage />);

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login?returnTo=/pricing/verify');
    });
    // The form must not render for a visitor who is being redirected.
    expect(screen.queryByLabelText(/academic email/i)).not.toBeInTheDocument();
  });

  it('does not redirect while auth is still loading', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false, isLoading: true });

    render(<StudentVerifyPage />);

    expect(mockPush).not.toHaveBeenCalled();
  });
});

// ===========================================================================
// Confirm page — app/verify/confirm/page.tsx
// ===========================================================================

describe('StudentVerifyConfirmPage (confirm)', () => {
  it('reads the token query param, confirms on 200, and shows the Subscribe as Student CTA', async () => {
    mockSearchParams = new URLSearchParams('token=raw-token-123');
    mockApi.post.mockResolvedValue({
      statusCode: 200,
      data: { eligible: true, expires_at: '2026-01-01T00:00:00Z' },
    });

    render(<StudentVerifyConfirmPage />);

    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalledWith('/api/verification/student/confirm', {
        token: 'raw-token-123',
      });
    });

    expect(await screen.findByText(/you.re verified/i)).toBeInTheDocument();
    const cta = screen.getByRole('link', { name: /subscribe as student/i });
    expect(cta).toHaveAttribute('href', '/pricing');
  });

  it('shows an error and a retry link on a 400 response', async () => {
    mockSearchParams = new URLSearchParams('token=bad-token');
    mockApi.post.mockResolvedValue({ statusCode: 400, data: { eligible: false, expires_at: null } });

    render(<StudentVerifyConfirmPage />);

    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalledWith('/api/verification/student/confirm', {
        token: 'bad-token',
      });
    });

    expect(await screen.findByText(/verification failed/i)).toBeInTheDocument();
    expect(screen.getByText(/invalid or has expired/i)).toBeInTheDocument();
    const retry = screen.getByRole('link', { name: /retry verification/i });
    expect(retry).toHaveAttribute('href', '/pricing/verify');
  });

  it('shows an error immediately and never calls the API when the token is missing', async () => {
    mockSearchParams = new URLSearchParams(); // no token

    render(<StudentVerifyConfirmPage />);

    expect(await screen.findByText(/verification failed/i)).toBeInTheDocument();
    expect(screen.getByText(/missing its token/i)).toBeInTheDocument();
    expect(mockApi.post).not.toHaveBeenCalled();
  });
});
