/**
 * Unit tests for admin TestimonialModeration + its review modal.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { TestimonialModeration } from '@/components/admin/TestimonialModeration';

jest.mock('@/lib/api', () => ({
  apiClient: { getAdminTestimonials: jest.fn(), updateTestimonialStatus: jest.fn() },
}));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function t(id: string, overrides: Record<string, unknown> = {}) {
  return {
    user_id: id,
    display_name: `Name ${id}`,
    quote: `Quote ${id}`,
    status: 'pending',
    submitted_at: '2026-01-01T00:00:00Z',
    linkedin_url: '',
    ...overrides,
  };
}

beforeEach(() => jest.clearAllMocks());

it('renders testimonials after loading', async () => {
  mockApi.getAdminTestimonials.mockResolvedValue({ data: { testimonials: [t('1'), t('2')] } as never, statusCode: 200 });
  render(<TestimonialModeration />);
  expect(await screen.findAllByText('Name 1')).not.toHaveLength(0);
});

it('shows error state with retry', async () => {
  mockApi.getAdminTestimonials.mockResolvedValue({ error: 'boom', statusCode: 500 });
  render(<TestimonialModeration />);
  expect(await screen.findByText('boom')).toBeInTheDocument();
  mockApi.getAdminTestimonials.mockResolvedValue({ data: { testimonials: [t('1')] } as never, statusCode: 200 });
  fireEvent.click(screen.getByRole('button', { name: /try again/i }));
  expect(await screen.findAllByText('Name 1')).not.toHaveLength(0);
});

it('filters by status tab', async () => {
  mockApi.getAdminTestimonials.mockResolvedValue({
    data: { testimonials: [t('1', { status: 'pending' }), t('2', { status: 'approved' })] } as never,
    statusCode: 200,
  });
  render(<TestimonialModeration />);
  await screen.findAllByText('Name 1');
  fireEvent.click(screen.getByRole('tab', { name: /filter testimonials by approved/i }));
  expect(screen.queryByText('Name 1')).not.toBeInTheDocument();
  expect(screen.getAllByText('Name 2').length).toBeGreaterThan(0);
});

it('shows empty state for a filter with no matches', async () => {
  mockApi.getAdminTestimonials.mockResolvedValue({
    data: { testimonials: [t('1', { status: 'pending' })] } as never,
    statusCode: 200,
  });
  render(<TestimonialModeration />);
  await screen.findAllByText('Name 1');
  fireEvent.click(screen.getByRole('tab', { name: /filter testimonials by approved/i }));
  expect(screen.getByText(/No approved testimonials/i)).toBeInTheDocument();
});

it('opens the review modal and approves a pending testimonial', async () => {
  mockApi.getAdminTestimonials.mockResolvedValue({ data: { testimonials: [t('1')] } as never, statusCode: 200 });
  mockApi.updateTestimonialStatus.mockResolvedValue({ data: { message: 'ok' } as never, statusCode: 200 });
  render(<TestimonialModeration />);
  const rows = await screen.findAllByText('Name 1');
  fireEvent.click(rows[0]);

  expect(await screen.findByText('Review Testimonial')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /approve testimonial from name 1/i }));
  await waitFor(() => expect(mockApi.updateTestimonialStatus).toHaveBeenCalledWith('1', 'approve', undefined));
});

it('surfaces an action error in the modal', async () => {
  mockApi.getAdminTestimonials.mockResolvedValue({ data: { testimonials: [t('1')] } as never, statusCode: 200 });
  mockApi.updateTestimonialStatus.mockResolvedValue({ error: 'rejected by server', statusCode: 500 });
  render(<TestimonialModeration />);
  const rows = await screen.findAllByText('Name 1');
  fireEvent.click(rows[0]);
  await screen.findByText('Review Testimonial');
  fireEvent.click(screen.getByRole('button', { name: /reject testimonial from name 1/i }));
  expect(await screen.findByText('rejected by server')).toBeInTheDocument();
});

it('shows a Revoke action for approved testimonials', async () => {
  mockApi.getAdminTestimonials.mockResolvedValue({
    data: { testimonials: [t('1', { status: 'approved' })] } as never,
    statusCode: 200,
  });
  render(<TestimonialModeration />);
  const rows = await screen.findAllByText('Name 1');
  fireEvent.click(rows[0]);
  await screen.findByText('Review Testimonial');
  expect(screen.getByRole('button', { name: /revoke testimonial from name 1/i })).toBeInTheDocument();
});
