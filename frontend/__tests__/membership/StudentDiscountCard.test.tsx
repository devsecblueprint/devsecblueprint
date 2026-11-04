/**
 * StudentDiscountCard — rendering and fallback tests (Task 18.3).
 *
 * Validates: Requirements 8.5, 8.6, 8.7, 8.9, 8.10
 *
 * Covers:
 *  - dynamic annual savings shown on the Annual toggle when both student
 *    monthly + annual prices exist (8.7);
 *  - discovery-failure / no-price state shows the "temporarily unavailable"
 *    message and no price (8.10);
 *  - interval-mismatch omits the computed savings-heading percent (8.9);
 *  - prices come from props, not hardcoded, when a price IS present (8.5/8.6).
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {
  StudentDiscountCard,
  type StudentDiscountProduct,
} from '@/app/pricing/StudentDiscountCard';
import { apiClient } from '@/lib/api';

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn(), prefetch: jest.fn() }),
}));
jest.mock('@/lib/api', () => ({ apiClient: { get: jest.fn(), post: jest.fn() } }));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function product(overrides: Partial<StudentDiscountProduct>): StudentDiscountProduct {
  return {
    id: 'prod_x',
    name: 'Student Builder',
    description: 'Discounted Builder',
    price: 1000,
    monthly_price: 1000,
    currency: 'usd',
    interval: 'month',
    dsb_tier: 'STUDENT_BUILDER',
    price_id: 'price_x',
    ...overrides,
  };
}

const studentMonthly = product({
  id: 'prod_sb_m',
  price: 1000, // $10.00/mo
  monthly_price: 1000,
  interval: 'month',
  price_id: 'price_sb_month',
});

const studentAnnual = product({
  id: 'prod_sb_y',
  price: 9600, // $96.00/yr
  monthly_price: 800, // $8.00/mo equivalent -> 20% annual savings
  interval: 'year',
  price_id: 'price_sb_year',
});

const builderMonthly = product({
  id: 'prod_b_m',
  name: 'Builder',
  dsb_tier: 'BUILDER',
  price: 2000, // $20.00/mo -> student $10 is 50% off
  monthly_price: 2000,
  interval: 'month',
  price_id: 'price_b_month',
});

const builderAnnual = product({
  id: 'prod_b_y',
  name: 'Builder',
  dsb_tier: 'BUILDER',
  price: 19200,
  monthly_price: 1600,
  interval: 'year',
  price_id: 'price_b_year',
});

/** Base props: unauthenticated so the eligibility fetch never fires. */
function baseProps() {
  return {
    studentMonthly: null as StudentDiscountProduct | null,
    studentAnnual: null as StudentDiscountProduct | null,
    builderMonthly: null as StudentDiscountProduct | null,
    builderAnnual: null as StudentDiscountProduct | null,
    isLoading: false,
    isAuthenticated: false,
    authLoading: false,
    subscriptionStatus: null as string | null,
  };
}

beforeEach(() => jest.clearAllMocks());

describe('StudentDiscountCard rendering and fallbacks', () => {
  it('shows the temporarily-unavailable state and no price when discovery fails (8.10)', () => {
    render(<StudentDiscountCard {...baseProps()} />);

    expect(
      screen.getByText(/student discount is temporarily unavailable/i)
    ).toBeInTheDocument();
    // No price text rendered.
    expect(screen.queryByText(/\$\d/)).not.toBeInTheDocument();
    // Eligibility is never fetched for an unauthenticated visitor.
    expect(mockApi.get).not.toHaveBeenCalled();
  });

  it('sources the displayed price from props, not hardcoded values (8.5/8.6)', () => {
    render(
      <StudentDiscountCard
        {...baseProps()}
        studentMonthly={studentMonthly}
        studentAnnual={studentAnnual}
      />
    );

    // Monthly price from props ($10.00), not a hardcoded figure.
    expect(screen.getByText('$10.00')).toBeInTheDocument();
    expect(screen.getByText('/month')).toBeInTheDocument();
    expect(
      screen.queryByText(/student discount is temporarily unavailable/i)
    ).not.toBeInTheDocument();
  });

  it('shows a dynamic annual-savings figure on the toggle when both prices exist (8.7)', () => {
    render(
      <StudentDiscountCard
        {...baseProps()}
        studentMonthly={studentMonthly}
        studentAnnual={studentAnnual}
      />
    );

    // 1 - (800 / 1000) = 20%.
    expect(screen.getByText(/Save 20%/)).toBeInTheDocument();
  });

  it('shows the computed savings heading when both tiers share the selected interval (8.8)', () => {
    render(
      <StudentDiscountCard
        {...baseProps()}
        studentMonthly={studentMonthly}
        studentAnnual={studentAnnual}
        builderMonthly={builderMonthly}
        builderAnnual={builderAnnual}
      />
    );

    // Default interval is monthly: builder $20 vs student $10 = 50%.
    expect(screen.getByText(/Students save ~50% on Builder/i)).toBeInTheDocument();
  });

  it('omits the computed savings-heading percent on interval mismatch (8.9)', async () => {
    const user = userEvent.setup();
    // Builder only has a monthly price; student only has an annual price.
    render(
      <StudentDiscountCard
        {...baseProps()}
        studentMonthly={null}
        studentAnnual={studentAnnual}
        builderMonthly={builderMonthly}
        builderAnnual={null}
      />
    );

    // Only one student interval -> no toggle; the selected interval defaults to
    // monthly but there is no student monthly price, so the student side of the
    // shared-interval comparison is undefined -> percent omitted.
    expect(screen.queryByText(/Students save ~/i)).not.toBeInTheDocument();
    // Falls back to the generic heading.
    expect(
      screen.getByText(/Discounted Builder pricing for students/i)
    ).toBeInTheDocument();
  });
});
