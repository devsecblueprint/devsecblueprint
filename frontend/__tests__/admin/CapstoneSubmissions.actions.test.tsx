/**
 * Complementary tests for CapstoneSubmissions — the interactive review/grant
 * flows not covered by the base render test.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient, type CapstoneSubmission } from '@/lib/api';
import { CapstoneSubmissions } from '@/components/admin/CapstoneSubmissions';

jest.mock('@/lib/api', () => ({
  apiClient: {
    getCapstoneSubmissions: jest.fn(),
    submitReview: jest.fn(),
    getReviewAdmin: jest.fn(),
    getCertificatePreview: jest.fn(),
    post: jest.fn(),
  },
}));
jest.mock('@/components/MarkdownRenderer', () => ({
  __esModule: true,
  default: ({ markdown }: { markdown: string }) => <div data-testid="md">{markdown}</div>,
}));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function submission(overrides: Partial<CapstoneSubmission> = {}): CapstoneSubmission {
  return {
    user_id: 'u1',
    content_id: 'devsecops-capstone',
    github_username: 'ada',
    repo_url: 'https://github.com/ada/project',
    submitted_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    status: 'pending_review',
    has_active_credential: false,
    credential_id: null,
    ...overrides,
  };
}

function listResponse(subs: CapstoneSubmission[]) {
  return { data: { submissions: subs, total_count: subs.length, page: 1, page_size: 50, total_pages: 1 }, statusCode: 200 };
}

beforeEach(() => jest.clearAllMocks());

it('submits a review and grants a credential on PASS', async () => {
  mockApi.getCapstoneSubmissions.mockResolvedValue(listResponse([submission()]));
  mockApi.submitReview.mockResolvedValue({ data: {} as never, statusCode: 200 });
  mockApi.post.mockResolvedValue({ data: {} as never, statusCode: 200 });

  render(<CapstoneSubmissions />);
  // Open the review modal (desktop + mobile each render a Review button)
  const reviewButtons = await screen.findAllByRole('button', { name: /^review$/i });
  fireEvent.click(reviewButtons[0]);

  // FeedbackModal with cert grading appears
  expect(await screen.findByText('Review Capstone Submission')).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText(/Feedback markdown editor/i), { target: { value: 'Excellent work overall.' } });
  fireEvent.click(screen.getByRole('button', { name: /^✓ Pass$/i }));
  fireEvent.click(screen.getByRole('button', { name: /submit & grant credential/i }));

  await waitFor(() => expect(mockApi.submitReview).toHaveBeenCalledWith('u1', 'devsecops-capstone', 'Excellent work overall.', 'passed'));
  // PASS also triggers the grant endpoint
  await waitFor(() =>
    expect(mockApi.post).toHaveBeenCalledWith(
      expect.stringContaining('/admin/certifications/candidates/u1/devsecops-engineering/grant'),
      {},
    ),
  );
});

it('loads and displays a review for a reviewed submission', async () => {
  mockApi.getCapstoneSubmissions.mockResolvedValue(listResponse([submission({ status: 'reviewed' })]));
  mockApi.getReviewAdmin.mockResolvedValue({
    data: { review: { feedback: '# Great', reviewed_by: 'admin', reviewed_at: '2026-01-02' } } as never,
    statusCode: 200,
  });

  render(<CapstoneSubmissions />);
  const viewButtons = await screen.findAllByRole('button', { name: /view review/i });
  fireEvent.click(viewButtons[0]);
  await waitFor(() => expect(mockApi.getReviewAdmin).toHaveBeenCalledWith('u1', 'devsecops-capstone'));
  expect(await screen.findByTestId('md')).toHaveTextContent('# Great');
});

it('grants a credential through the confirmation modal', async () => {
  mockApi.getCapstoneSubmissions.mockResolvedValue(listResponse([submission({ status: 'reviewed' })]));
  mockApi.post.mockResolvedValue({ data: {} as never, statusCode: 200 });

  render(<CapstoneSubmissions />);
  const grantButtons = await screen.findAllByRole('button', { name: /grant cert/i });
  fireEvent.click(grantButtons[0]);

  // GrantCertificateModal confirmation
  expect(await screen.findByRole('heading', { name: 'Grant Certificate' })).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /^grant certificate$/i }));
  await waitFor(() =>
    expect(mockApi.post).toHaveBeenCalledWith(
      expect.stringContaining('/admin/certifications/candidates/u1/devsecops-engineering/grant'),
      {},
    ),
  );
});

it('opens the certificate preview for a submission with an active credential', async () => {
  mockApi.getCapstoneSubmissions.mockResolvedValue(
    listResponse([submission({ status: 'passed', has_active_credential: true, credential_id: 'CRED-1' })]),
  );
  mockApi.getCertificatePreview.mockResolvedValue({
    data: { preview_url: 'https://cdn/cert.png', credential_id: 'CRED-1' } as never,
    statusCode: 200,
  });

  render(<CapstoneSubmissions />);
  const viewCert = await screen.findAllByRole('button', { name: /view cert/i });
  fireEvent.click(viewCert[0]);
  await waitFor(() => expect(mockApi.getCertificatePreview).toHaveBeenCalledWith('CRED-1'));
});
