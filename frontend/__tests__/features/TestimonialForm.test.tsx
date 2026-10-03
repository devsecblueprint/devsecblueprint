/**
 * Unit tests for the TestimonialForm modal.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { TestimonialForm } from '@/components/features/TestimonialForm';

jest.mock('@/lib/api', () => ({
  apiClient: {
    getMyTestimonial: jest.fn(),
    submitTestimonial: jest.fn(),
  },
}));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

beforeEach(() => jest.clearAllMocks());

it('renders nothing when closed', () => {
  const { container } = render(<TestimonialForm isOpen={false} onClose={jest.fn()} />);
  expect(container).toBeEmptyDOMElement();
});

it('shows the empty form when the user has no testimonial (404)', async () => {
  mockApi.getMyTestimonial.mockResolvedValue({ error: 'not found', statusCode: 404 });
  render(<TestimonialForm isOpen onClose={jest.fn()} />);
  expect(await screen.findByText('Share Your Testimonial')).toBeInTheDocument();
  expect(screen.getByLabelText(/Your Testimonial/i)).toBeInTheDocument();
});

it('shows a read-only view for an approved testimonial', async () => {
  mockApi.getMyTestimonial.mockResolvedValue({
    data: {
      testimonial: {
        display_name: 'Ada',
        quote: 'Great platform',
        status: 'approved',
        linkedin_url: 'https://linkedin.com/in/ada',
      },
    } as never,
    statusCode: 200,
  });
  render(<TestimonialForm isOpen onClose={jest.fn()} />);
  expect(await screen.findByText('Your Testimonial')).toBeInTheDocument();
  expect(screen.getByText('Approved')).toBeInTheDocument();
  expect(screen.getByText('Great platform')).toBeInTheDocument();
});

it('pre-populates an editable form for a pending testimonial', async () => {
  mockApi.getMyTestimonial.mockResolvedValue({
    data: {
      testimonial: {
        display_name: 'Ada',
        quote: 'Pending quote',
        status: 'pending',
        linkedin_url: '',
      },
    } as never,
    statusCode: 200,
  });
  render(<TestimonialForm isOpen onClose={jest.fn()} />);
  expect(await screen.findByText('Pending Review')).toBeInTheDocument();
  expect(screen.getByDisplayValue('Pending quote')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /update testimonial/i })).toBeInTheDocument();
});

it('validates required quote before submitting', async () => {
  mockApi.getMyTestimonial.mockResolvedValue({ error: 'not found', statusCode: 404 });
  render(<TestimonialForm isOpen onClose={jest.fn()} />);
  const submitBtn = await screen.findByRole('button', { name: /submit testimonial/i });

  // Submit with an empty quote
  fireEvent.click(submitBtn);

  expect(await screen.findByText(/quote is required/i)).toBeInTheDocument();
  expect(mockApi.submitTestimonial).not.toHaveBeenCalled();
});

it('submits a valid testimonial and shows the thank-you state', async () => {
  mockApi.getMyTestimonial.mockResolvedValue({ error: 'not found', statusCode: 404 });
  mockApi.submitTestimonial.mockResolvedValue({ data: { message: 'ok' } as never, statusCode: 201 });
  const { container } = render(<TestimonialForm isOpen onClose={jest.fn()} />);
  await screen.findByText('Share Your Testimonial');

  fireEvent.change(container.querySelector('#displayName')!, { target: { value: 'Ada Lovelace' } });
  fireEvent.change(container.querySelector('#quote')!, {
    target: { value: 'This platform is excellent for learning.' },
  });
  fireEvent.click(screen.getByRole('button', { name: /submit testimonial/i }));

  expect(await screen.findByText('Thank You!')).toBeInTheDocument();
  expect(mockApi.submitTestimonial).toHaveBeenCalledWith(
    expect.objectContaining({ display_name: 'Ada Lovelace' }),
  );
});

it('submits as Anonymous when the toggle is checked', async () => {
  mockApi.getMyTestimonial.mockResolvedValue({ error: 'not found', statusCode: 404 });
  mockApi.submitTestimonial.mockResolvedValue({ data: { message: 'ok' } as never, statusCode: 201 });
  const { container } = render(<TestimonialForm isOpen onClose={jest.fn()} />);
  await screen.findByText('Share Your Testimonial');

  fireEvent.click(screen.getByLabelText(/Submit anonymously/i));
  fireEvent.change(container.querySelector('#quote')!, {
    target: { value: 'Anonymous but positive feedback here.' },
  });
  fireEvent.click(screen.getByRole('button', { name: /submit testimonial/i }));

  await waitFor(() => expect(mockApi.submitTestimonial).toHaveBeenCalled());
  expect(mockApi.submitTestimonial).toHaveBeenCalledWith(
    expect.objectContaining({ display_name: 'Anonymous' }),
  );
});

it('surfaces a submit error from the API', async () => {
  mockApi.getMyTestimonial.mockResolvedValue({ error: 'not found', statusCode: 404 });
  mockApi.submitTestimonial.mockResolvedValue({ error: 'duplicate', statusCode: 409 });
  const { container } = render(<TestimonialForm isOpen onClose={jest.fn()} />);
  await screen.findByText('Share Your Testimonial');

  fireEvent.change(container.querySelector('#displayName')!, { target: { value: 'Ada' } });
  fireEvent.change(container.querySelector('#quote')!, {
    target: { value: 'A perfectly valid testimonial quote.' },
  });
  fireEvent.click(screen.getByRole('button', { name: /submit testimonial/i }));

  expect(await screen.findByText('duplicate')).toBeInTheDocument();
});

it('calls onClose when the close button is clicked', async () => {
  const onClose = jest.fn();
  mockApi.getMyTestimonial.mockResolvedValue({ error: 'not found', statusCode: 404 });
  render(<TestimonialForm isOpen onClose={onClose} />);
  await screen.findByText('Share Your Testimonial');
  fireEvent.click(screen.getByLabelText(/Close modal/i));
  expect(onClose).toHaveBeenCalled();
});
