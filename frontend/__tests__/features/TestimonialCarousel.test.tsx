/**
 * Unit tests for the TestimonialCarousel.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { TestimonialCarousel } from '@/components/features/TestimonialCarousel';

jest.mock('@/lib/api', () => ({ apiClient: { getApprovedTestimonials: jest.fn() } }));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function testimonial(name: string, overrides: Record<string, unknown> = {}) {
  return { display_name: name, quote: `Quote by ${name}`, linkedin_url: '', avatar_url: '', ...overrides };
}

beforeEach(() => jest.clearAllMocks());

it('shows the placeholder when there are no approved testimonials', async () => {
  mockApi.getApprovedTestimonials.mockResolvedValue({ data: { testimonials: [] } as never, statusCode: 200 });
  render(<TestimonialCarousel />);
  expect(await screen.findByText(/Testimonials are on the way/i)).toBeInTheDocument();
});

it('renders testimonial cards', async () => {
  mockApi.getApprovedTestimonials.mockResolvedValue({
    data: { testimonials: [testimonial('Ada'), testimonial('Grace')] } as never,
    statusCode: 200,
  });
  render(<TestimonialCarousel />);
  expect(await screen.findByText('Quote by Ada')).toBeInTheDocument();
  expect(screen.getByText('Quote by Grace')).toBeInTheDocument();
});

it('renders a LinkedIn link for non-anonymous testimonials with a url', async () => {
  mockApi.getApprovedTestimonials.mockResolvedValue({
    data: { testimonials: [testimonial('Ada', { linkedin_url: 'https://linkedin.com/in/ada' })] } as never,
    statusCode: 200,
  });
  render(<TestimonialCarousel />);
  const link = await screen.findByRole('link', { name: 'Ada' });
  expect(link).toHaveAttribute('href', 'https://linkedin.com/in/ada');
});

it('renders anonymous testimonials without a link', async () => {
  mockApi.getApprovedTestimonials.mockResolvedValue({
    data: { testimonials: [testimonial('Anonymous', { linkedin_url: 'https://linkedin.com/in/x' })] } as never,
    statusCode: 200,
  });
  render(<TestimonialCarousel />);
  await screen.findByText('Quote by Anonymous');
  expect(screen.queryByRole('link', { name: 'Anonymous' })).not.toBeInTheDocument();
});

it('shows navigation controls when there are more cards than fit in view', async () => {
  // jsdom innerWidth is 1024 -> 3 cards per view; 4 testimonials -> scrolling needed
  mockApi.getApprovedTestimonials.mockResolvedValue({
    data: { testimonials: [testimonial('A'), testimonial('B'), testimonial('C'), testimonial('D')] } as never,
    statusCode: 200,
  });
  render(<TestimonialCarousel />);
  await screen.findByText('Quote by A');
  expect(screen.getByRole('button', { name: /next testimonial/i })).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /next testimonial/i }));
  // Still rendered (index advanced); dots exist
  expect(screen.getAllByRole('tab').length).toBeGreaterThan(0);
});

it('silently renders the placeholder if the fetch throws', async () => {
  mockApi.getApprovedTestimonials.mockRejectedValue(new Error('network'));
  render(<TestimonialCarousel />);
  expect(await screen.findByText(/Testimonials are on the way/i)).toBeInTheDocument();
});
