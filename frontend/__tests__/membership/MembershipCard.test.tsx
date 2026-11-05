/**
 * MembershipCard — Student Builder rendering tests.
 *
 * Covers the dashboard Membership card additions for the Student Builder tier:
 *  - a student role with an academic email renders "Student Builder", the
 *    academic email, and the "Verified on X, valid through Y" line;
 *  - the "Re-verify academic email" link appears when eligibility is expired or
 *    within 30 days of expiry, and NOT when expiry is far in the future;
 *  - a student role WITHOUT an academic email renders the card (no email block)
 *    and does not throw;
 *  - builder / free / admin render as before, with the sky badge reserved for
 *    student and amber kept for the others.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { MembershipCard } from '@/components/dashboard/MembershipCard';

// next/link renders a plain anchor in tests.
jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ href, children, ...rest }: any) => (
    <a href={typeof href === 'string' ? href : '#'} {...rest}>
      {children}
    </a>
  ),
}));

// Fixed "now" so the re-verify window math is deterministic.
const NOW = new Date('2025-06-01T00:00:00Z').getTime();
beforeAll(() => {
  jest.spyOn(Date, 'now').mockReturnValue(NOW);
});
afterAll(() => {
  jest.restoreAllMocks();
});

function daysFromNow(days: number): string {
  return new Date(NOW + days * 24 * 60 * 60 * 1000).toISOString();
}

describe('MembershipCard — Student Builder', () => {
  it('renders the Student Builder label, academic email, and verified/valid-through line', () => {
    render(
      <MembershipCard
        role="student"
        isAdmin={false}
        academicEmail="student@uni.edu"
        verifiedAt="2025-01-15T00:00:00Z"
        eligibilityExpiresAt={daysFromNow(200)}
      />
    );

    expect(screen.getByText('Student Builder')).toBeInTheDocument();
    expect(screen.getByText('student@uni.edu')).toBeInTheDocument();
    // Dates are formatted en-US long (e.g. "January 15, 2025"). Compute the
    // expected strings the same way the component does so the assertion is
    // independent of the test runner's local timezone.
    const fmt = (iso: string) =>
      new Date(iso).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    const verified = fmt('2025-01-15T00:00:00Z');
    const valid = fmt(daysFromNow(200));
    expect(
      screen.getByText(`Verified on ${verified}, valid through ${valid}`)
    ).toBeInTheDocument();
  });

  it('shows the Re-verify link when expiry is within 30 days', () => {
    render(
      <MembershipCard
        role="student"
        isAdmin={false}
        academicEmail="student@uni.edu"
        verifiedAt="2025-01-15T00:00:00Z"
        eligibilityExpiresAt={daysFromNow(10)}
      />
    );

    const link = screen.getByRole('link', { name: 'Re-verify academic email' });
    expect(link).toHaveAttribute('href', '/pricing/verify');
  });

  it('shows the Re-verify link when eligibility is already expired', () => {
    render(
      <MembershipCard
        role="student"
        isAdmin={false}
        academicEmail="student@uni.edu"
        verifiedAt="2024-01-15T00:00:00Z"
        eligibilityExpiresAt={daysFromNow(-5)}
      />
    );

    expect(
      screen.getByRole('link', { name: 'Re-verify academic email' })
    ).toBeInTheDocument();
  });

  it('does NOT show the Re-verify link when expiry is far in the future', () => {
    render(
      <MembershipCard
        role="student"
        isAdmin={false}
        academicEmail="student@uni.edu"
        verifiedAt="2025-01-15T00:00:00Z"
        eligibilityExpiresAt={daysFromNow(200)}
      />
    );

    expect(
      screen.queryByRole('link', { name: 'Re-verify academic email' })
    ).not.toBeInTheDocument();
  });

  it('renders the student card without the email block when academicEmail is missing', () => {
    expect(() =>
      render(
        <MembershipCard
          role="student"
          isAdmin={false}
          academicEmail={null}
          verifiedAt={null}
          eligibilityExpiresAt={null}
        />
      )
    ).not.toThrow();

    expect(screen.getByText('Student Builder')).toBeInTheDocument();
    expect(screen.queryByText(/Academic email:/)).not.toBeInTheDocument();
    expect(
      screen.queryByRole('link', { name: 'Re-verify academic email' })
    ).not.toBeInTheDocument();
  });

  it('uses a sky badge for student and an amber badge for other roles', () => {
    const { rerender } = render(
      <MembershipCard role="student" isAdmin={false} academicEmail="student@uni.edu" />
    );
    const studentBadge = screen.getByText('Student Builder');
    expect(studentBadge.className).toContain('bg-sky-100');
    expect(studentBadge.className).not.toContain('bg-amber-100');

    rerender(<MembershipCard role="builder" isAdmin={false} />);
    const builderBadge = screen.getByText('Builder');
    expect(builderBadge.className).toContain('bg-amber-100');
    expect(builderBadge.className).not.toContain('bg-sky-100');
  });

  it('renders builder, free, and admin roles as before', () => {
    const { rerender } = render(<MembershipCard role="builder" isAdmin={false} />);
    expect(screen.getByText('Builder')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();

    rerender(<MembershipCard role="free" isAdmin={false} />);
    expect(screen.getByText('Free')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Explore Builder/ })).toBeInTheDocument();

    rerender(<MembershipCard role="free" isAdmin={true} />);
    expect(screen.getByText('Admin')).toBeInTheDocument();
  });

  it('admin override wins even when role is student', () => {
    render(
      <MembershipCard
        role="student"
        isAdmin={true}
        academicEmail="student@uni.edu"
        eligibilityExpiresAt={daysFromNow(200)}
      />
    );
    expect(screen.getByText('Admin')).toBeInTheDocument();
    expect(screen.queryByText('Student Builder')).not.toBeInTheDocument();
    // No student-only email block when admin override is active.
    expect(screen.queryByText('student@uni.edu')).not.toBeInTheDocument();
  });
});
