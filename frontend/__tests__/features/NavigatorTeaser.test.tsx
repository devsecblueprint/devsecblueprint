/**
 * Unit tests for NavigatorTeaser CTA configuration handling.
 */
import { render, screen } from '@testing-library/react';
import { NavigatorTeaser } from '@/components/features/NavigatorTeaser';

const ENV_KEY = 'NEXT_PUBLIC_NAVIGATOR_INTEREST_FORM_URL';
const VALID = 'https://docs.google.com/forms/d/e/abc123/viewform';

afterEach(() => {
  delete process.env[ENV_KEY];
  jest.restoreAllMocks();
});

it('renders the CTA as a safe new-tab link when configured', () => {
  process.env[ENV_KEY] = VALID;
  render(<NavigatorTeaser />);
  const link = screen.getByRole('link', { name: /join the interest list/i });
  expect(link).toHaveAttribute('href', VALID);
  expect(link).toHaveAttribute('target', '_blank');
  expect(link).toHaveAttribute('rel', expect.stringContaining('noopener'));
  expect(link).toHaveAttribute('rel', expect.stringContaining('noreferrer'));
});

it('keeps the teaser but hides the CTA when unconfigured', () => {
  jest.spyOn(console, 'warn').mockImplementation(() => {});
  render(<NavigatorTeaser />);
  expect(screen.getByText('Your next move deserves a blueprint.')).toBeInTheDocument();
  expect(screen.getByText(/applications not yet open/i)).toBeInTheDocument();
  expect(screen.queryByRole('link')).not.toBeInTheDocument();
});

it('rejects editor URLs and non-Google URLs', () => {
  jest.spyOn(console, 'warn').mockImplementation(() => {});
  for (const bad of ['https://docs.google.com/forms/d/abc123/edit', 'https://example.com/form']) {
    process.env[ENV_KEY] = bad;
    const { unmount } = render(<NavigatorTeaser />);
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
    unmount();
  }
});
