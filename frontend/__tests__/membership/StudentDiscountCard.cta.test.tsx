/**
 * StudentDiscountCard — CTA state-machine tests (Task 19.2).
 *
 * Validates: Requirements 8.11, 8.12, 8.13, 8.14
 *
 * The card derives its CTA from the visitor's auth state, the eligibility
 * lookup (GET /api/verification/student/eligibility, fetched on mount when
 * authenticated), and the subscription status passed as a prop:
 *
 *  8.11 not authenticated           -> "Verify Student Status",
 *                                      click -> router.push('/login?returnTo=/pricing/verify')
 *  8.12 authenticated + not eligible-> "Verify Student Status",
 *                                      click -> router.push('/pricing/verify')
 *  8.13 authenticated + eligible +  -> "Subscribe as Student",
 *       no active/past_due sub         click -> POST /api/stripe/checkout then redirect
 *  8.14 authenticated + active/      -> CTA hidden (no duplicate membership)
 *       past_due sub
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {
  StudentDiscountCard,
  type StudentDiscountProduct,
} from '@/app/pricing/StudentDiscountCard';
import { apiClient } from '@/lib/api';

const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, replace: jest.fn(), prefetch: jest.fn() }),
}));
jest.mock('@/lib/api', () => ({ apiClient: { get: jest.fn(), post: jest.fn() } }));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

const studentMonthly: StudentDiscountProduct = {
  id: 'prod_sb_m',
  name: 'Student Builder',
  description: 'Discounted Builder',
  price: 1000,
  monthly_price: 1000,
  currency: 'usd',
  interval: 'month',
  dsb_tier: 'STUDENT_BUILDER',
  price_id: 'price_sb_month',
};

function baseProps() {
  return {
    studentMonthly,
    studentAnnual: null as StudentDiscountProduct | null,
    builderMonthly: null as StudentDiscountProduct | null,
    builderAnnual: null as StudentDiscountProduct | null,
    isLoading: false,
    isAuthenticated: false,
    authLoading: false,
    subscriptionStatus: null as string | null,
  };
}

/** Make the eligibility GET resolve with the given `eligible` flag. */
function mockEligibility(eligible: boolean) {
  mockApi.get.mockResolvedValue({
    data: { eligible, expires_at: eligible ? '2999-01-01T00:00:00Z' : null } as never,
    statusCode: 200,
  });
}

// jsdom marks window.location.href as read-only; make it assignable so the
// checkout redirect can be observed without a navigation error.
const originalLocation = window.location;
beforeAll(() => {
  Object.defineProperty(window, 'location', {
    configurable: true,
    writable: true,
    value: { ...originalLocation, href: '' },
  });
});
afterAll(() => {
  Object.defineProperty(window, 'location', {
    configurable: true,
    writable: true,
    value: originalLocation,
  });
});

beforeEach(() => {
  jest.clearAllMocks();
  window.location.href = '';
});

describe('StudentDiscountCard CTA state machine', () => {
  it('not authenticated -> "Verify Student Status" routes through login then verify (8.11)', async () => {
    const user = userEvent.setup();
    render(<StudentDiscountCard {...baseProps()} isAuthenticated={false} />);

    const cta = screen.getByRole('button', { name: 'Verify Student Status' });
    await user.click(cta);

    expect(mockPush).toHaveBeenCalledWith('/login?returnTo=/pricing/verify');
    // Unauthenticated visitors never fetch eligibility.
    expect(mockApi.get).not.toHaveBeenCalled();
  });

  it('authenticated + not eligible -> "Verify Student Status" starts verification (8.12)', async () => {
    const user = userEvent.setup();
    mockEligibility(false);

    render(<StudentDiscountCard {...baseProps()} isAuthenticated={true} />);

    await waitFor(() =>
      expect(mockApi.get).toHaveBeenCalledWith('/api/verification/student/eligibility')
    );

    const cta = screen.getByRole('button', { name: 'Verify Student Status' });
    await user.click(cta);

    expect(mockPush).toHaveBeenCalledWith('/pricing/verify');
    expect(mockApi.post).not.toHaveBeenCalled();
  });

  it('authenticated + eligible + no active sub -> "Subscribe as Student" starts checkout (8.13)', async () => {
    const user = userEvent.setup();
    mockEligibility(true);
    mockApi.post.mockResolvedValue({
      data: { checkout_url: 'https://checkout.stripe.com/session_123' } as never,
      statusCode: 200,
    });

    render(
      <StudentDiscountCard
        {...baseProps()}
        isAuthenticated={true}
        subscriptionStatus={null}
      />
    );

    const cta = await screen.findByRole('button', { name: 'Subscribe as Student' });
    await user.click(cta);

    await waitFor(() =>
      expect(mockApi.post).toHaveBeenCalledWith('/api/stripe/checkout', {
        price_id: 'price_sb_month',
        dsb_tier: 'STUDENT_BUILDER',
        interval: 'month',
      })
    );
    await waitFor(() =>
      expect(window.location.href).toBe('https://checkout.stripe.com/session_123')
    );
    // Checkout does not route through the verify flow.
    expect(mockPush).not.toHaveBeenCalled();
  });

  it('authenticated + active subscription -> CTA hidden (8.14)', async () => {
    mockEligibility(true);

    render(
      <StudentDiscountCard
        {...baseProps()}
        isAuthenticated={true}
        subscriptionStatus="active"
      />
    );

    // Give the eligibility effect a chance to run.
    await waitFor(() => expect(mockApi.get).toHaveBeenCalled());

    expect(
      screen.queryByRole('button', { name: /Subscribe as Student|Verify Student Status/ })
    ).not.toBeInTheDocument();
  });

  it('authenticated + past_due subscription -> CTA hidden (8.14)', async () => {
    mockEligibility(true);

    render(
      <StudentDiscountCard
        {...baseProps()}
        isAuthenticated={true}
        subscriptionStatus="past_due"
      />
    );

    await waitFor(() => expect(mockApi.get).toHaveBeenCalled());

    expect(
      screen.queryByRole('button', { name: /Subscribe as Student|Verify Student Status/ })
    ).not.toBeInTheDocument();
  });
});
