/**
 * Unit tests for admin WalkthroughStatistics.
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { WalkthroughStatistics } from '@/components/admin/WalkthroughStatistics';

jest.mock('@/lib/api', () => ({ apiClient: { getWalkthroughStatistics: jest.fn() } }));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

beforeEach(() => jest.clearAllMocks());

it('renders statistics with the mapped walkthrough title', async () => {
  mockApi.getWalkthroughStatistics.mockResolvedValue({
    data: { completed_count: 12, in_progress_count: 5, most_popular_walkthrough: 'aws-detective-control' },
    statusCode: 200,
  });
  render(<WalkthroughStatistics />);
  expect(await screen.findByText('12')).toBeInTheDocument();
  expect(screen.getByText('5')).toBeInTheDocument();
  expect(screen.getByText('Event-Driven S3 Public Access Detective Control')).toBeInTheDocument();
});

it('shows the unmapped id when no title mapping exists', async () => {
  mockApi.getWalkthroughStatistics.mockResolvedValue({
    data: { completed_count: 0, in_progress_count: 0, most_popular_walkthrough: 'custom-wt' },
    statusCode: 200,
  });
  render(<WalkthroughStatistics />);
  expect(await screen.findByText('custom-wt')).toBeInTheDocument();
});

it('shows "No data available" when there is no popular walkthrough', async () => {
  mockApi.getWalkthroughStatistics.mockResolvedValue({
    data: { completed_count: 0, in_progress_count: 0, most_popular_walkthrough: null },
    statusCode: 200,
  });
  render(<WalkthroughStatistics />);
  expect(await screen.findByText('No data available')).toBeInTheDocument();
});

it('shows an error state with retry', async () => {
  mockApi.getWalkthroughStatistics.mockResolvedValue({ error: 'boom', statusCode: 500 });
  render(<WalkthroughStatistics />);
  expect(await screen.findByText('Failed to Load Statistics')).toBeInTheDocument();
  mockApi.getWalkthroughStatistics.mockResolvedValue({
    data: { completed_count: 1, in_progress_count: 0, most_popular_walkthrough: null },
    statusCode: 200,
  });
  fireEvent.click(screen.getByRole('button', { name: /try again/i }));
  expect(await screen.findByText('1')).toBeInTheDocument();
});
