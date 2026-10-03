/**
 * Unit tests for the dashboard WalkthroughsSection.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { getWalkthroughsWithProgress } from '@/lib/walkthrough-client';
import { WalkthroughsSection } from '@/components/dashboard/WalkthroughsSection';

jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
}));
jest.mock('@/lib/walkthrough-client', () => ({ getWalkthroughsWithProgress: jest.fn() }));
jest.mock('@/components/dashboard/WalkthroughPreviewModal', () => ({
  WalkthroughPreviewModal: ({ walkthrough }: { walkthrough: { title: string } }) => (
    <div data-testid="preview-modal">{walkthrough.title}</div>
  ),
}));
const mockGet = getWalkthroughsWithProgress as jest.Mock;

function wt(id: string, status: string, overrides: Record<string, unknown> = {}) {
  return {
    id,
    title: `Walkthrough ${id}`,
    difficulty: 'Beginner',
    estimatedTime: 30,
    topics: [],
    progress: { status },
    ...overrides,
  };
}

beforeEach(() => jest.clearAllMocks());

it('shows an empty prompt when there are no in-progress walkthroughs', async () => {
  mockGet.mockResolvedValue([wt('1', 'not_started')]);
  render(<WalkthroughsSection />);
  expect(await screen.findByText(/Start a hands-on walkthrough/i)).toBeInTheDocument();
});

it('shows in-progress walkthroughs with a preview button', async () => {
  mockGet.mockResolvedValue([wt('1', 'in_progress'), wt('2', 'in_progress')]);
  render(<WalkthroughsSection />);
  expect(await screen.findByText('Walkthrough 1')).toBeInTheDocument();
  expect(screen.getAllByRole('button', { name: /preview/i }).length).toBe(2);
});

it('shows an all-completed celebration', async () => {
  mockGet.mockResolvedValue([wt('1', 'completed'), wt('2', 'completed')]);
  render(<WalkthroughsSection />);
  expect(await screen.findByText(/All walkthroughs completed/i)).toBeInTheDocument();
});

it('shows an error fallback prompt', async () => {
  mockGet.mockRejectedValue(new Error('fail'));
  render(<WalkthroughsSection />);
  expect(await screen.findByText(/Start a hands-on walkthrough/i)).toBeInTheDocument();
});

it('opens the preview modal when a Preview button is clicked', async () => {
  mockGet.mockResolvedValue([wt('1', 'in_progress')]);
  render(<WalkthroughsSection />);
  fireEvent.click(await screen.findByRole('button', { name: /preview/i }));
  expect(screen.getByTestId('preview-modal')).toHaveTextContent('Walkthrough 1');
});

it('shows a View All link when more than 3 are in progress', async () => {
  mockGet.mockResolvedValue([
    wt('1', 'in_progress'), wt('2', 'in_progress'), wt('3', 'in_progress'), wt('4', 'in_progress'),
  ]);
  render(<WalkthroughsSection />);
  await screen.findByText('Walkthrough 1');
  expect(screen.getByText(/View All/i)).toBeInTheDocument();
  // Only 3 cards displayed
  expect(screen.getAllByRole('button', { name: /preview/i }).length).toBe(3);
});
