/**
 * Unit tests for CapstoneSubmissionForm.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useAuth } from '@/lib/hooks/useAuth';
import { apiClient } from '@/lib/api';
import { CapstoneSubmissionForm } from '@/components/CapstoneSubmissionForm';

jest.mock('@/lib/hooks/useAuth', () => ({ useAuth: jest.fn() }));
jest.mock('@/lib/api', () => ({
  apiClient: {
    get: jest.fn(),
    getUserProfile: jest.fn(),
    getCapstoneSubmission: jest.fn(),
    getCapstoneReview: jest.fn(),
    saveProgress: jest.fn(),
  },
}));

const mockUseAuth = useAuth as jest.Mock;
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function authAs(overrides: Record<string, unknown> = {}) {
  mockUseAuth.mockReturnValue({
    username: 'ada',
    providerUsername: 'ada',
    provider: 'github',
    isAuthenticated: true,
    ...overrides,
  });
}

/** Grant Builder tier via active subscription. */
function grantBuilder() {
  mockApi.get.mockResolvedValue({
    data: { membership_tier: 'BUILDER', subscription_status: 'active' } as never,
    statusCode: 200,
  });
}

beforeEach(() => {
  jest.clearAllMocks();
  mockApi.getCapstoneSubmission.mockResolvedValue({ data: {} as never, statusCode: 200 });
});

it('renders nothing when unauthenticated', () => {
  authAs({ isAuthenticated: false, providerUsername: null });
  const { container } = render(<CapstoneSubmissionForm contentId="c1" />);
  expect(container).toBeEmptyDOMElement();
});

it('shows an upgrade prompt for non-Builder users', async () => {
  authAs();
  // No active subscription, no contributor role
  mockApi.get.mockResolvedValue({ data: { status: 'inactive' } as never, statusCode: 200 });
  mockApi.getUserProfile.mockResolvedValue({ data: { contributor_role: null } as never, statusCode: 200 });

  render(<CapstoneSubmissionForm contentId="c1" />);
  expect(await screen.findByText(/available to Builder members/i)).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /upgrade to builder/i })).toHaveAttribute('href', '/pricing');
});

it('grants access to contributors even without a subscription', async () => {
  authAs();
  mockApi.get.mockResolvedValue({ data: { status: 'inactive' } as never, statusCode: 200 });
  mockApi.getUserProfile.mockResolvedValue({
    data: { contributor_role: { role: 'author' } } as never,
    statusCode: 200,
  });

  render(<CapstoneSubmissionForm contentId="c1" />);
  expect(await screen.findByRole('button', { name: /submit project/i })).toBeInTheDocument();
});

it('shows the submission form for a Builder with no prior submission', async () => {
  authAs();
  grantBuilder();
  render(<CapstoneSubmissionForm contentId="c1" />);
  expect(await screen.findByLabelText(/Repository URL/i)).toBeInTheDocument();
});

it('validates the repo URL belongs to the user', async () => {
  authAs();
  grantBuilder();
  render(<CapstoneSubmissionForm contentId="c1" />);
  const input = await screen.findByLabelText(/Repository URL/i);
  fireEvent.change(input, { target: { value: 'https://github.com/someone-else/project' } });
  expect(await screen.findByText(/under your GitHub account/i)).toBeInTheDocument();
});

it('submits a valid repo URL successfully', async () => {
  authAs();
  grantBuilder();
  mockApi.saveProgress.mockResolvedValue({ data: { message: 'ok' }, statusCode: 200 });
  const onSubmitSuccess = jest.fn();

  render(<CapstoneSubmissionForm contentId="c1" onSubmitSuccess={onSubmitSuccess} />);
  const input = await screen.findByLabelText(/Repository URL/i);
  fireEvent.change(input, { target: { value: 'https://github.com/ada/project' } });
  fireEvent.click(screen.getByRole('button', { name: /submit project/i }));

  await waitFor(() => expect(mockApi.saveProgress).toHaveBeenCalledWith('c1', 'https://github.com/ada/project'));
  expect(await screen.findByText(/under review/i)).toBeInTheDocument();
  expect(onSubmitSuccess).toHaveBeenCalled();
});

it('shows a 409 conflict message when submission is locked for review', async () => {
  authAs();
  grantBuilder();
  mockApi.saveProgress.mockResolvedValue({ error: 'conflict', statusCode: 409 });

  render(<CapstoneSubmissionForm contentId="c1" />);
  const input = await screen.findByLabelText(/Repository URL/i);
  fireEvent.change(input, { target: { value: 'https://github.com/ada/project' } });
  fireEvent.click(screen.getByRole('button', { name: /submit project/i }));

  expect(await screen.findByText(/currently under review/i)).toBeInTheDocument();
});

it('shows the pending-review read-only state for an existing submission', async () => {
  authAs();
  grantBuilder();
  mockApi.getCapstoneSubmission.mockResolvedValue({
    data: { repo_url: 'https://github.com/ada/project', status: 'pending_review' } as never,
    statusCode: 200,
  });

  render(<CapstoneSubmissionForm contentId="c1" />);
  expect(await screen.findByText(/under review/i)).toBeInTheDocument();
  expect(screen.getByText('https://github.com/ada/project')).toBeInTheDocument();
});
