/**
 * Unit tests for CertificationStats.
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { CertificationStats } from '@/app/admin/components/certifications/CertificationStats';

jest.mock('@/lib/api', () => ({ apiClient: { get: jest.fn() } }));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

const STATS = {
  candidates_by_status: { IN_PROGRESS: 3, AWARDED: 2 },
  credentials_by_status: { ACTIVE: 4 },
  pending_reviews: 1,
};

beforeEach(() => jest.clearAllMocks());

it('shows a loading skeleton', () => {
  mockApi.get.mockReturnValue(new Promise(() => {}));
  const { container } = render(<CertificationStats />);
  expect(container.querySelector('[aria-busy="true"]')).toBeInTheDocument();
});

it('renders totals and status breakdown', async () => {
  mockApi.get.mockResolvedValue({ data: STATS as never, statusCode: 200 });
  render(<CertificationStats />);
  // total candidates = 3 + 2 = 5
  expect(await screen.findByText('5')).toBeInTheDocument();
  expect(screen.getByText('Total Candidates')).toBeInTheDocument();
  // credentials = 4 (also appears in the ACTIVE breakdown, so use getAllByText)
  expect(screen.getAllByText('4').length).toBeGreaterThan(0);
  expect(screen.getByText('Credentials Issued')).toBeInTheDocument();
  // pending = 1
  expect(screen.getByText('Pending Reviews')).toBeInTheDocument();
  // breakdown label formatted
  expect(screen.getByText('In Progress')).toBeInTheDocument();
});

it('shows an error state with retry', async () => {
  mockApi.get.mockResolvedValue({ error: 'boom', statusCode: 500 });
  render(<CertificationStats />);
  expect(await screen.findByText(/Failed to load certification stats/i)).toBeInTheDocument();
  mockApi.get.mockResolvedValue({ data: STATS as never, statusCode: 200 });
  fireEvent.click(screen.getByRole('button', { name: /retry/i }));
  expect(await screen.findByText('Total Candidates')).toBeInTheDocument();
});
