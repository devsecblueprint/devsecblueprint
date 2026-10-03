/**
 * Unit tests for WalkthroughBrowser (filtering, pagination, access gating).
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { WalkthroughBrowser } from '@/components/WalkthroughBrowser';

const replaceMock = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({ replace: replaceMock }),
  useSearchParams: () => new URLSearchParams(),
}));

function wt(id: string, overrides: Record<string, unknown> = {}) {
  return {
    id,
    title: `Walkthrough ${id}`,
    description: `Description for ${id}`,
    difficulty: 'Beginner',
    estimatedTime: 30,
    topics: ['aws', 'security'],
    progress: { status: 'not_started' },
    ...overrides,
  };
}

function makeMany(n: number) {
  return Array.from({ length: n }, (_, i) => wt(String(i + 1)));
}

beforeEach(() => jest.clearAllMocks());

it('renders all walkthroughs and the results count', () => {
  render(<WalkthroughBrowser initialWalkthroughs={[wt('1'), wt('2')] as never} />);
  expect(screen.getByText('Walkthrough 1')).toBeInTheDocument();
  expect(screen.getByText('Walkthrough 2')).toBeInTheDocument();
  expect(screen.getByText(/of 2 walkthroughs/i)).toBeInTheDocument();
});

it('filters by search query', () => {
  render(
    <WalkthroughBrowser
      initialWalkthroughs={[wt('1', { title: 'Kubernetes Lab' }), wt('2', { title: 'AWS IAM Lab' })] as never}
    />,
  );
  fireEvent.change(screen.getByLabelText('Search walkthroughs'), { target: { value: 'kubernetes' } });
  expect(screen.getByText('Kubernetes Lab')).toBeInTheDocument();
  expect(screen.queryByText('AWS IAM Lab')).not.toBeInTheDocument();
});

it('filters by difficulty', () => {
  render(
    <WalkthroughBrowser
      initialWalkthroughs={[wt('1', { difficulty: 'Beginner' }), wt('2', { difficulty: 'Advanced' })] as never}
    />,
  );
  fireEvent.change(screen.getByLabelText('Filter by difficulty'), { target: { value: 'Advanced' } });
  expect(screen.queryByText('Walkthrough 1')).not.toBeInTheDocument();
  expect(screen.getByText('Walkthrough 2')).toBeInTheDocument();
});

it('filters by progress status', () => {
  render(
    <WalkthroughBrowser
      initialWalkthroughs={[
        wt('1', { progress: { status: 'completed' } }),
        wt('2', { progress: { status: 'not_started' } }),
      ] as never}
    />,
  );
  fireEvent.change(screen.getByLabelText('Filter by progress status'), { target: { value: 'completed' } });
  expect(screen.getByText('Walkthrough 1')).toBeInTheDocument();
  expect(screen.queryByText('Walkthrough 2')).not.toBeInTheDocument();
});

it('shows an empty message and a clear-filters button when nothing matches', () => {
  render(<WalkthroughBrowser initialWalkthroughs={[wt('1')] as never} />);
  fireEvent.change(screen.getByLabelText('Search walkthroughs'), { target: { value: 'zzzznomatch' } });
  expect(screen.getByText(/No walkthroughs match your filters/i)).toBeInTheDocument();

  fireEvent.click(screen.getByRole('button', { name: /clear all filters/i }));
  expect(screen.getByText('Walkthrough 1')).toBeInTheDocument();
});

it('paginates when there are more than 12 walkthroughs', () => {
  render(<WalkthroughBrowser initialWalkthroughs={makeMany(13) as never} />);
  // page 1 shows first 12
  expect(screen.getByText('Walkthrough 1')).toBeInTheDocument();
  expect(screen.queryByText('Walkthrough 13')).not.toBeInTheDocument();

  fireEvent.click(screen.getByRole('button', { name: /go to page 2/i }));
  expect(screen.getByText('Walkthrough 13')).toBeInTheDocument();
});

it('shows a locked badge and upgrade prompt for Builder-locked walkthroughs without access', () => {
  render(
    <WalkthroughBrowser
      initialWalkthroughs={[wt('1')] as never}
      lockedWalkthroughs={{ '1': 'BUILDER' }}
      membershipTier="FREE"
    />,
  );
  expect(screen.getByText('Upgrade to Access')).toBeInTheDocument();
});

it('grants access to a locked walkthrough for Builder members', () => {
  render(
    <WalkthroughBrowser
      initialWalkthroughs={[wt('1')] as never}
      lockedWalkthroughs={{ '1': 'BUILDER' }}
      membershipTier="BUILDER"
    />,
  );
  expect(screen.queryByText('Upgrade to Access')).not.toBeInTheDocument();
  expect(screen.getByText('View Walkthrough')).toBeInTheDocument();
});
