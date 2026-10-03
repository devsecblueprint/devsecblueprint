/**
 * Unit tests for the certification ReviewOutcomeForm.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { ReviewOutcomeForm } from '@/app/admin/components/certifications/ReviewOutcomeForm';

jest.mock('@/lib/api', () => ({ apiClient: { post: jest.fn() } }));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function renderForm(overrides: Partial<React.ComponentProps<typeof ReviewOutcomeForm>> = {}) {
  const onComplete = overrides.onComplete ?? jest.fn();
  const onCancel = overrides.onCancel ?? jest.fn();
  render(<ReviewOutcomeForm userId="u1" pathwayId="p1" onComplete={onComplete} onCancel={onCancel} />);
  return { onComplete, onCancel };
}

beforeEach(() => jest.clearAllMocks());

it('renders decision options and rubric dimensions', () => {
  renderForm();
  expect(screen.getByText('Record Review Outcome')).toBeInTheDocument();
  expect(screen.getByText('Passed')).toBeInTheDocument();
  expect(screen.getByText('Architecture & Design')).toBeInTheDocument();
  expect(screen.getByText('Technical Depth & Understanding')).toBeInTheDocument();
});

it('disables submit until a decision is selected', () => {
  renderForm();
  expect(screen.getByRole('button', { name: /submit review outcome/i })).toBeDisabled();
  fireEvent.click(screen.getByRole('radio', { name: /passed/i }));
  expect(screen.getByRole('button', { name: /submit review outcome/i })).toBeEnabled();
});

it('submits the review payload with scores and notes', async () => {
  mockApi.post.mockResolvedValue({ data: {} as never, statusCode: 200 });
  const { onComplete } = renderForm();

  fireEvent.click(screen.getByRole('radio', { name: /passed/i }));
  fireEvent.change(screen.getByLabelText(/Score for Architecture & Design/i), { target: { value: '9/10' } });
  fireEvent.change(screen.getByLabelText(/Comment for Architecture & Design/i), { target: { value: 'solid' } });
  fireEvent.change(screen.getByLabelText(/Assessment for Technical Depth/i), { target: { value: 'strong' } });

  fireEvent.click(screen.getByRole('button', { name: /submit review outcome/i }));

  await waitFor(() => expect(mockApi.post).toHaveBeenCalled());
  const [url, body] = mockApi.post.mock.calls[0] as [string, Record<string, unknown>];
  expect(url).toContain('/admin/certifications/candidates/u1/p1/review-outcome');
  expect(body.status).toBe('PASSED');
  expect((body.rubric_scores as Record<string, unknown>).architecture).toEqual({ score: '9/10', comment: 'solid' });
  expect((body.evaluation_dimensions as Record<string, unknown>).technical_depth).toBe('strong');
  expect(onComplete).toHaveBeenCalled();
});

it('surfaces a submit error', async () => {
  mockApi.post.mockResolvedValue({ error: 'server error', statusCode: 500 });
  renderForm();
  fireEvent.click(screen.getByRole('radio', { name: /revisions required/i }));
  fireEvent.click(screen.getByRole('button', { name: /submit review outcome/i }));
  expect(await screen.findByText('server error')).toBeInTheDocument();
});

it('calls onCancel from the cancel buttons', () => {
  const { onCancel } = renderForm();
  // There are two Cancel controls (header + footer); either should work.
  fireEvent.click(screen.getAllByRole('button', { name: /^cancel$/i })[0]);
  expect(onCancel).toHaveBeenCalled();
});
