/**
 * Unit tests for PathwayCard.
 */
import { render, screen } from '@testing-library/react';
import { PathwayCard } from '@/app/components/certification/PathwayCard';

jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href, ...rest }: { children: React.ReactNode; href: string }) => (
    <a href={href} {...rest}>{children}</a>
  ),
}));

it('renders the pathway name, description, and status label', () => {
  render(
    <PathwayCard
      pathway_id="devsecops-engineering"
      display_name="DevSecOps Engineering"
      description="Build secure pipelines"
      candidate_status="IN_PROGRESS"
    />,
  );
  expect(screen.getByText('DevSecOps Engineering')).toBeInTheDocument();
  expect(screen.getByText('Build secure pipelines')).toBeInTheDocument();
  expect(screen.getByText('In Progress')).toBeInTheDocument();
});

it('links to the pathway detail page', () => {
  render(
    <PathwayCard pathway_id="dsb-champion" display_name="DSB Champion" description="d" candidate_status="AWARDED" />,
  );
  expect(screen.getByRole('link')).toHaveAttribute('href', '/dashboard/certifications/detail?pathway=dsb-champion');
});

it('maps each status to a readable label', () => {
  const statuses: Array<[PathwayCardProps['candidate_status'], string]> = [
    ['NOT_STARTED', 'Not Started'],
    ['ELIGIBLE_FOR_AWARD', 'Eligible for Award'],
    ['AWARDED', 'Awarded'],
    ['EXPIRED', 'Expired'],
    ['REVOKED', 'Revoked'],
  ];
  for (const [status, label] of statuses) {
    const { unmount } = render(
      <PathwayCard pathway_id="p" display_name="P" description="d" candidate_status={status} />,
    );
    expect(screen.getByText(label)).toBeInTheDocument();
    unmount();
  }
});

type PathwayCardProps = React.ComponentProps<typeof PathwayCard>;
