/**
 * Unit tests for the certification PathwayCard tile (components/certification).
 */
import { render, screen } from '@testing-library/react';
import { PathwayCard } from '@/components/certification/PathwayCard';
import type { PathwayWithStatus } from '@/components/certification/PathwayCard';

jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href, className }: { children: React.ReactNode; href: string; className?: string }) => (
    <a href={href} className={className}>{children}</a>
  ),
}));

function pathway(overrides: Partial<PathwayWithStatus> = {}): PathwayWithStatus {
  return {
    pathway_id: 'devsecops',
    display_name: 'DevSecOps Pathway',
    description: 'desc',
    candidate_status: 'IN_PROGRESS',
    ...overrides,
  };
}

it('renders the pathway name and status badge', () => {
  render(<PathwayCard pathway={pathway()} />);
  expect(screen.getByText('DevSecOps Pathway')).toBeInTheDocument();
  expect(screen.getByText('In Progress')).toBeInTheDocument();
});

it('links to the detail page', () => {
  render(<PathwayCard pathway={pathway({ pathway_id: 'cloud-sec' })} />);
  expect(screen.getByRole('link')).toHaveAttribute('href', '/dashboard/certifications/detail?pathway=cloud-sec');
});

it('shows the correct label for each status', () => {
  const cases: Array<[PathwayWithStatus['candidate_status'], string]> = [
    ['NOT_STARTED', 'Not Started'],
    ['ELIGIBLE_FOR_AWARD', 'Eligible'],
    ['AWARDED', 'Awarded'],
    ['EXPIRED', 'Expired'],
    ['REVOKED', 'Revoked'],
    [null, 'Not Started'],
  ];
  for (const [status, label] of cases) {
    const { unmount } = render(<PathwayCard pathway={pathway({ candidate_status: status })} />);
    expect(screen.getByText(label)).toBeInTheDocument();
    unmount();
  }
});
