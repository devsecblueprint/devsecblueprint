/**
 * Unit tests for FAQClient — search filtering, no-results, and analytics.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import FAQClient from '@/app/about/faq/FAQClient';
import { FAQ_CATEGORIES } from '@/lib/data/faq';
import { trackFAQEvent } from '@/lib/utils/faq-analytics';

jest.mock('@/lib/utils/faq-analytics', () => ({ trackFAQEvent: jest.fn() }));
const mockTrack = trackFAQEvent as jest.Mock;

const firstCategory = FAQ_CATEGORIES[0];
const firstQuestion = firstCategory.questions[0];

beforeEach(() => jest.clearAllMocks());

it('renders categories by default', () => {
  render(<FAQClient />);
  expect(screen.getAllByText(firstCategory.name).length).toBeGreaterThan(0);
});

it('shows a no-results message for a non-matching query (after debounce)', async () => {
  render(<FAQClient />);
  fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'zzzznotarealquery' } });
  expect(await screen.findByText(/No questions found/i)).toBeInTheDocument();
});

it('emits a search_no_results analytics event when nothing matches', async () => {
  render(<FAQClient />);
  fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'zzzznotarealquery' } });
  await waitFor(() =>
    expect(mockTrack).toHaveBeenCalledWith(expect.objectContaining({ type: 'search_no_results' })),
  );
});

it('emits a search_performed event when matches exist', async () => {
  render(<FAQClient />);
  const term = firstQuestion.question.split(' ').find((w) => w.length > 4) || 'the';
  fireEvent.change(screen.getByRole('searchbox'), { target: { value: term } });
  await waitFor(() =>
    expect(mockTrack).toHaveBeenCalledWith(expect.objectContaining({ type: 'search_performed' })),
  );
});

it('keeps a matching question visible after filtering', async () => {
  render(<FAQClient />);
  const term = firstQuestion.question.split(' ').find((w) => w.length > 5) || firstQuestion.question;
  fireEvent.change(screen.getByRole('searchbox'), { target: { value: term } });
  await waitFor(() => expect(screen.getAllByText(firstQuestion.question).length).toBeGreaterThan(0));
});
