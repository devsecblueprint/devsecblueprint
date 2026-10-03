/**
 * Unit tests for the SponsorshipInquiryForm component.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SponsorshipInquiryForm } from '@/components/ui/SponsorshipInquiryForm';
import { OPPORTUNITY_OPTIONS, BUDGET_OPTIONS } from '@/lib/data/sponsorship-data';

function fillValid() {
  fireEvent.change(screen.getByLabelText(/Full Name/i), { target: { value: 'Ada Lovelace' } });
  fireEvent.change(screen.getByLabelText(/Work Email/i), { target: { value: 'ada@company.com' } });
  fireEvent.change(screen.getByLabelText(/Company \/ Organization/i), { target: { value: 'Acme' } });
  fireEvent.change(screen.getByLabelText(/Sponsorship Opportunity/i), {
    target: { value: OPPORTUNITY_OPTIONS[0].value },
  });
  fireEvent.change(screen.getByLabelText(/Estimated Budget Range/i), {
    target: { value: BUDGET_OPTIONS[0].value },
  });
  fireEvent.change(screen.getByLabelText(/Partnership Goals/i), {
    target: { value: 'We want to reach security engineers.' },
  });
}

it('shows required errors on empty submit', async () => {
  render(<SponsorshipInquiryForm />);
  fireEvent.click(screen.getByRole('button', { name: /submit sponsorship inquiry/i }));
  const errs = await screen.findAllByText('This field is required');
  // fullName, email, company, opportunityType, budgetRange, goals
  expect(errs.length).toBeGreaterThanOrEqual(6);
});

it('validates the optional website URL scheme', async () => {
  render(<SponsorshipInquiryForm />);
  fillValid();
  fireEvent.change(screen.getByLabelText(/Company Website/i), { target: { value: 'ftp://bad' } });
  fireEvent.click(screen.getByRole('button', { name: /submit sponsorship inquiry/i }));
  expect(await screen.findByText(/must start with http/i)).toBeInTheDocument();
});

it('accepts a valid https website and submits', async () => {
  const onSubmit = jest.fn().mockResolvedValue({ success: true });
  render(<SponsorshipInquiryForm onSubmit={onSubmit} />);
  fillValid();
  fireEvent.change(screen.getByLabelText(/Company Website/i), { target: { value: 'https://acme.com' } });
  fireEvent.click(screen.getByRole('button', { name: /submit sponsorship inquiry/i }));
  await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
  expect(await screen.findByText(/Inquiry Submitted Successfully/i)).toBeInTheDocument();
});

it('rejects goals shorter than 10 chars', async () => {
  render(<SponsorshipInquiryForm />);
  fillValid();
  fireEvent.change(screen.getByLabelText(/Partnership Goals/i), { target: { value: 'short' } });
  fireEvent.click(screen.getByRole('button', { name: /submit sponsorship inquiry/i }));
  expect(await screen.findByText(/at least 10 characters/i)).toBeInTheDocument();
});

it('shows the default configuration error when no handler is provided', async () => {
  render(<SponsorshipInquiryForm />);
  fillValid();
  fireEvent.click(screen.getByRole('button', { name: /submit sponsorship inquiry/i }));
  expect(await screen.findByText(/endpoint not configured/i)).toBeInTheDocument();
});

it('shows a generic error when the handler throws', async () => {
  const onSubmit = jest.fn().mockRejectedValue(new Error('x'));
  render(<SponsorshipInquiryForm onSubmit={onSubmit} />);
  fillValid();
  fireEvent.click(screen.getByRole('button', { name: /submit sponsorship inquiry/i }));
  expect(await screen.findByText(/unexpected error occurred/i)).toBeInTheDocument();
});
