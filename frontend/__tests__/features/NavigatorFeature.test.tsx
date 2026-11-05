/**
 * Unit tests for the featured DSB Navigator pricing band.
 *
 * Verifies the interest-list CTA is a safe new-tab link to the configured
 * Google Form, that the program copy renders, and that no payment/enrollment
 * affordance is introduced.
 */
import { render, screen } from '@testing-library/react';
import { NavigatorFeature } from '@/components/features/NavigatorFeature';

const ENV_KEY = 'NEXT_PUBLIC_NAVIGATOR_INTEREST_FORM_URL';
const FORM_URL = 'https://forms.gle/5bM5NV5XrqqNSS1a6';

afterEach(() => {
  delete process.env[ENV_KEY];
  jest.restoreAllMocks();
});

it('renders the interest-list CTA as a safe new-tab link to the Google Form', () => {
  process.env[ENV_KEY] = FORM_URL;
  render(<NavigatorFeature />);

  const link = screen.getByRole('link', { name: /join the interest list/i });
  expect(link).toHaveAttribute('href', FORM_URL);
  expect(link).toHaveAttribute('target', '_blank');
  expect(link).toHaveAttribute('rel', expect.stringContaining('noopener'));
  expect(link).toHaveAttribute('rel', expect.stringContaining('noreferrer'));
  expect(link.textContent).toMatch(/opens in a new tab/i);
});

it('renders the program headline, eyebrow, highlights, and disclaimer', () => {
  process.env[ENV_KEY] = FORM_URL;
  render(<NavigatorFeature />);

  expect(screen.getByText('Your next move deserves a blueprint.')).toBeInTheDocument();
  expect(screen.getByText(/coming soon · dsb navigator/i)).toBeInTheDocument();
  expect(screen.getByText(/12-week mentorship experience/i)).toBeInTheDocument();
  expect(screen.getByText(/personalized development roadmap/i)).toBeInTheDocument();
  expect(screen.getByText(/technical and career guidance/i)).toBeInTheDocument();
  expect(screen.getByText(/limited founding cohort/i)).toBeInTheDocument();
  expect(screen.getByText(/applications are not open/i)).toBeInTheDocument();
});

it('keeps the program copy but hides the CTA when the form URL is unconfigured', () => {
  jest.spyOn(console, 'warn').mockImplementation(() => {});
  render(<NavigatorFeature />);

  expect(screen.getByText('Your next move deserves a blueprint.')).toBeInTheDocument();
  expect(screen.queryByRole('link')).not.toBeInTheDocument();
});

it('introduces no payment or enrollment control (discovery only)', () => {
  process.env[ENV_KEY] = FORM_URL;
  render(<NavigatorFeature />);

  // No buttons at all — the only affordance is the external interest-list link.
  expect(screen.queryByRole('button')).not.toBeInTheDocument();
  expect(screen.queryByText(/subscribe|checkout|enroll|\$/i)).not.toBeInTheDocument();
});
