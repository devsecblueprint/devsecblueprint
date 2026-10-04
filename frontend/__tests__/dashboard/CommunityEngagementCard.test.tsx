/**
 * Unit tests for CommunityEngagementCard.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { CommunityEngagementCard } from '@/components/dashboard/CommunityEngagementCard';

jest.mock('@/lib/api', () => ({ apiClient: { getMyTestimonial: jest.fn() } }));
jest.mock('@/components/features/TestimonialForm', () => ({
  TestimonialForm: ({ isOpen }: { isOpen: boolean }) => (isOpen ? <div data-testid="testimonial-modal" /> : null),
}));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

beforeEach(() => jest.clearAllMocks());

it('renders the quick-link cards', async () => {
  mockApi.getMyTestimonial.mockResolvedValue({ error: 'not found', statusCode: 404 });
  render(<CommunityEngagementCard />);
  expect(screen.getByText('Community & Engagement')).toBeInTheDocument();
  expect(screen.getByText('Star on GitHub')).toBeInTheDocument();
  expect(screen.getByText('Merch Store')).toBeInTheDocument();
  expect(await screen.findByText('Share Your Success Story')).toBeInTheDocument();
});

it('opens the testimonial modal from the share card', async () => {
  mockApi.getMyTestimonial.mockResolvedValue({ error: 'not found', statusCode: 404 });
  render(<CommunityEngagementCard />);
  fireEvent.click(await screen.findByLabelText(/share your success story/i));
  expect(screen.getByTestId('testimonial-modal')).toBeInTheDocument();
});

it('shows a pending-story state when a testimonial is pending', async () => {
  mockApi.getMyTestimonial.mockResolvedValue({ data: { status: 'pending' } as never, statusCode: 200 });
  render(<CommunityEngagementCard />);
  expect(await screen.findByText('Story Pending')).toBeInTheDocument();
});

it('shows a live-story state when a testimonial is approved', async () => {
  mockApi.getMyTestimonial.mockResolvedValue({ data: { status: 'approved' } as never, statusCode: 200 });
  render(<CommunityEngagementCard />);
  expect(await screen.findByText(/Story Live/i)).toBeInTheDocument();
});
