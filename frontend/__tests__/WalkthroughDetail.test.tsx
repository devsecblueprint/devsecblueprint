/**
 * Unit tests for WalkthroughDetail.
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { WalkthroughDetail } from '@/components/WalkthroughDetail';

const pushMock = jest.fn();
jest.mock('next/navigation', () => ({ useRouter: () => ({ push: pushMock }) }));
jest.mock('@/components/READMERenderer', () => ({
  READMERenderer: ({ markdown }: { markdown: string }) => <div data-testid="readme">{markdown}</div>,
}));

function walkthrough(overrides: Record<string, unknown> = {}) {
  return {
    id: 'wt-1',
    title: 'AWS IAM Lab',
    description: 'Learn IAM',
    difficulty: 'Intermediate',
    estimatedTime: 45,
    topics: ['aws', 'iam'],
    authors: [{ name: 'Ada', url: 'https://example.com/ada' }],
    prerequisites: ['Basic AWS'],
    repositoryUrl: 'https://github.com/x/y',
    readme: '# Lab readme',
    progress: { status: 'in_progress', startedAt: '2026-01-01T00:00:00Z', completedAt: null },
    ...overrides,
  };
}

beforeEach(() => jest.clearAllMocks());

it('renders title, description, difficulty, status, and topics', () => {
  render(<WalkthroughDetail walkthrough={walkthrough() as never} onMarkComplete={jest.fn()} />);
  expect(screen.getByRole('heading', { name: 'AWS IAM Lab' })).toBeInTheDocument();
  expect(screen.getByText('Learn IAM')).toBeInTheDocument();
  expect(screen.getByText('Intermediate')).toBeInTheDocument();
  expect(screen.getByText('In Progress')).toBeInTheDocument();
  expect(screen.getByText('aws')).toBeInTheDocument();
});

it('renders authors with links and prerequisites', () => {
  render(<WalkthroughDetail walkthrough={walkthrough() as never} onMarkComplete={jest.fn()} />);
  expect(screen.getByRole('link', { name: 'Ada' })).toHaveAttribute('href', 'https://example.com/ada');
  expect(screen.getByText('Basic AWS')).toBeInTheDocument();
});

it('renders the README when present', () => {
  render(<WalkthroughDetail walkthrough={walkthrough() as never} onMarkComplete={jest.fn()} />);
  expect(screen.getByTestId('readme')).toHaveTextContent('# Lab readme');
});

it('shows a fallback when the README is missing', () => {
  render(<WalkthroughDetail walkthrough={walkthrough({ readme: '' }) as never} onMarkComplete={jest.fn()} />);
  expect(screen.getByText(/Documentation not available/i)).toBeInTheDocument();
});

it('navigates back to walkthroughs', () => {
  render(<WalkthroughDetail walkthrough={walkthrough() as never} onMarkComplete={jest.fn()} />);
  fireEvent.click(screen.getByRole('button', { name: /back to walkthroughs/i }));
  expect(pushMock).toHaveBeenCalledWith('/walkthroughs');
});

it('calls onMarkComplete for in-progress walkthroughs', () => {
  const onMarkComplete = jest.fn();
  render(<WalkthroughDetail walkthrough={walkthrough() as never} onMarkComplete={onMarkComplete} />);
  fireEvent.click(screen.getByRole('button', { name: /mark walkthrough as complete/i }));
  expect(onMarkComplete).toHaveBeenCalled();
});

it('hides the mark-complete button when not in progress', () => {
  render(
    <WalkthroughDetail
      walkthrough={walkthrough({ progress: { status: 'completed', completedAt: '2026-02-01T00:00:00Z' } }) as never}
      onMarkComplete={jest.fn()}
    />,
  );
  expect(screen.queryByRole('button', { name: /mark walkthrough as complete/i })).not.toBeInTheDocument();
  expect(screen.getByText('Completed')).toBeInTheDocument();
});
