/**
 * Unit tests for CertificationCandidates (filtered/paginated table).
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { CertificationCandidates } from '@/app/admin/components/certifications/CertificationCandidates';

jest.mock('@/lib/api', () => ({ apiClient: { get: jest.fn() } }));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function candidate(id: string, overrides: Record<string, unknown> = {}) {
  return {
    user_id: id,
    display_name: `Candidate ${id}`,
    pathway_id: 'devsecops-engineering',
    pathway_display_name: 'DevSecOps Engineering Pathway',
    candidate_status: 'IN_PROGRESS',
    review_session_status: 'PENDING_REVIEW',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

function resp(candidates: unknown[], has_more = false) {
  return { data: { candidates, page: 1, limit: 20, has_more }, statusCode: 200 };
}

beforeEach(() => jest.clearAllMocks());

it('renders candidates after loading', async () => {
  mockApi.get.mockResolvedValue(resp([candidate('1'), candidate('2')]));
  render(<CertificationCandidates onSelectCandidate={jest.fn()} />);
  expect(await screen.findAllByText('Candidate 1')).not.toHaveLength(0);
});

it('shows the empty state', async () => {
  mockApi.get.mockResolvedValue(resp([]));
  render(<CertificationCandidates onSelectCandidate={jest.fn()} />);
  expect(await screen.findByText(/No certification candidates found/i)).toBeInTheDocument();
});

it('shows error state with retry', async () => {
  mockApi.get.mockResolvedValue({ error: 'boom', statusCode: 500 });
  render(<CertificationCandidates onSelectCandidate={jest.fn()} />);
  expect(await screen.findByText('Failed to Load Candidates')).toBeInTheDocument();
  mockApi.get.mockResolvedValue(resp([candidate('1')]));
  fireEvent.click(screen.getByRole('button', { name: /try again/i }));
  expect(await screen.findAllByText('Candidate 1')).not.toHaveLength(0);
});

it('filters by pathway (resets page and refetches)', async () => {
  mockApi.get.mockResolvedValue(resp([candidate('1')]));
  render(<CertificationCandidates onSelectCandidate={jest.fn()} />);
  await screen.findAllByText('Candidate 1');
  fireEvent.change(screen.getByLabelText(/Filter by pathway/i), { target: { value: 'dsb-champion' } });
  await waitFor(() => {
    const lastUrl = mockApi.get.mock.calls.at(-1)![0] as string;
    expect(lastUrl).toContain('pathway=dsb-champion');
  });
});

it('selects a candidate on row click', async () => {
  const onSelect = jest.fn();
  mockApi.get.mockResolvedValue(resp([candidate('1')]));
  render(<CertificationCandidates onSelectCandidate={onSelect} />);
  const rows = await screen.findAllByRole('button', { name: /view details for Candidate 1/i });
  fireEvent.click(rows[0]);
  expect(onSelect).toHaveBeenCalledWith('1', 'devsecops-engineering');
});

it('enables Next when there are more pages', async () => {
  mockApi.get.mockResolvedValue(resp([candidate('1')], true));
  render(<CertificationCandidates onSelectCandidate={jest.fn()} />);
  await screen.findAllByText('Candidate 1');
  const next = screen.getByRole('button', { name: /next/i });
  expect(next).toBeEnabled();
  fireEvent.click(next);
  await waitFor(() => {
    const lastUrl = mockApi.get.mock.calls.at(-1)![0] as string;
    expect(lastUrl).toContain('page=2');
  });
});
