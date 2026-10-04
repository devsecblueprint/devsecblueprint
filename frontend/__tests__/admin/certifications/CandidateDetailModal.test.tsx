/**
 * Unit tests for CandidateDetailModal.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { CandidateDetailModal } from '@/app/admin/components/certifications/CandidateDetailModal';

jest.mock('@/lib/api', () => ({ apiClient: { get: jest.fn(), post: jest.fn() } }));
jest.mock('@/app/admin/components/certifications/ReviewOutcomeForm', () => ({
  ReviewOutcomeForm: ({ onComplete, onCancel }: { onComplete: () => void; onCancel: () => void }) => (
    <div data-testid="review-form">
      <button onClick={onComplete}>complete-review</button>
      <button onClick={onCancel}>cancel-review</button>
    </div>
  ),
}));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function detail(overrides: Record<string, unknown> = {}) {
  return {
    candidate: {
      pathway_id: 'devsecops-engineering',
      candidate_status: 'IN_PROGRESS',
      review_gate: { status: 'PENDING_REVIEW', reviewed_at: null, reviewer_id: null },
      started_at: '2026-01-01',
      updated_at: '2026-01-02',
      credential_id: null,
      prior_credential_id: null,
      display_name: 'Ada Lovelace',
    },
    review_history: [
      { revision_number: 1, status: 'PENDING_REVIEW', submission_url: 'https://github.com/ada/x', submitted_at: '2026-01-01', reviewed_at: null },
    ],
    credential: null,
    ...overrides,
  };
}

function renderModal(props: Partial<React.ComponentProps<typeof CandidateDetailModal>> = {}) {
  const onClose = props.onClose ?? jest.fn();
  const onActionComplete = props.onActionComplete ?? jest.fn();
  render(
    <CandidateDetailModal
      isOpen
      onClose={onClose}
      userId="u1"
      pathwayId="devsecops-engineering"
      onActionComplete={onActionComplete}
      {...props}
    />,
  );
  return { onClose, onActionComplete };
}

beforeEach(() => jest.clearAllMocks());

it('renders nothing when closed', () => {
  const { container } = render(
    <CandidateDetailModal isOpen={false} onClose={jest.fn()} userId="u1" pathwayId="p1" onActionComplete={jest.fn()} />,
  );
  expect(container).toBeEmptyDOMElement();
});

it('loads and renders candidate detail', async () => {
  mockApi.get.mockResolvedValue({ data: detail() as never, statusCode: 200 });
  renderModal();
  expect(await screen.findByText('Ada Lovelace')).toBeInTheDocument();
  expect(screen.getByText('DevSecOps Engineering Pathway')).toBeInTheDocument();
  expect(screen.getByText('Revision #1')).toBeInTheDocument();
});

it('shows an error with retry', async () => {
  mockApi.get.mockResolvedValue({ error: 'boom', statusCode: 500 });
  renderModal();
  expect(await screen.findByText('boom')).toBeInTheDocument();
  mockApi.get.mockResolvedValue({ data: detail() as never, statusCode: 200 });
  fireEvent.click(screen.getByRole('button', { name: /retry/i }));
  expect(await screen.findByText('Ada Lovelace')).toBeInTheDocument();
});

it('opens the review form when PENDING_REVIEW and records the outcome', async () => {
  mockApi.get.mockResolvedValue({ data: detail() as never, statusCode: 200 });
  const { onActionComplete } = renderModal();
  await screen.findByText('Ada Lovelace');
  fireEvent.click(screen.getByRole('button', { name: /record review outcome/i }));
  expect(screen.getByTestId('review-form')).toBeInTheDocument();
  fireEvent.click(screen.getByText('complete-review'));
  await waitFor(() => expect(onActionComplete).toHaveBeenCalled());
});

it('grants a credential', async () => {
  mockApi.get.mockResolvedValue({ data: detail() as never, statusCode: 200 });
  mockApi.post.mockResolvedValue({ data: { status: 'ok', credential_id: 'CRED-123' } as never, statusCode: 200 });
  const { onActionComplete } = renderModal();
  await screen.findByText('Ada Lovelace');
  fireEvent.click(screen.getByRole('button', { name: /grant credential/i }));
  await waitFor(() => expect(mockApi.post).toHaveBeenCalled());
  expect(await screen.findByText(/Credential granted successfully: CRED-123/)).toBeInTheDocument();
  expect(onActionComplete).toHaveBeenCalled();
});

it('renders credential details and a revoke action when awarded', async () => {
  mockApi.get.mockResolvedValue({
    data: detail({
      candidate: {
        pathway_id: 'devsecops-engineering',
        candidate_status: 'AWARDED',
        review_gate: { status: 'PASSED', reviewed_at: '2026-01-02', reviewer_id: 'admin' },
        started_at: '2026-01-01',
        updated_at: '2026-01-02',
        credential_id: 'CRED-1',
        prior_credential_id: null,
        display_name: 'Ada',
      },
      credential: {
        credential_id: 'CRED-1',
        pathway_id: 'devsecops-engineering',
        credential_status: 'ACTIVE',
        issued_at: '2026-01-02',
        expires_at: '2027-01-02',
      },
    }) as never,
    statusCode: 200,
  });
  renderModal();
  await screen.findByText('Ada');
  expect(screen.getByText('CRED-1')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /revoke credential/i })).toBeInTheDocument();
  // Grant should NOT appear when awarded
  expect(screen.queryByRole('button', { name: /grant credential/i })).not.toBeInTheDocument();
});
