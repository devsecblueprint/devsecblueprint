/**
 * Unit tests for the ContactForm component.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ContactForm } from '@/components/ui/ContactForm';

function fillValid() {
  fireEvent.change(screen.getByLabelText(/Full Name/i), { target: { value: 'Ada Lovelace' } });
  fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: 'ada@example.com' } });
  fireEvent.change(screen.getByLabelText(/Inquiry Type/i), { target: { value: 'general-inquiry' } });
  fireEvent.change(screen.getByLabelText(/Subject/i), { target: { value: 'Hello' } });
  fireEvent.change(screen.getByLabelText(/Message/i), {
    target: { value: 'This is a sufficiently long message.' },
  });
}

describe('validation', () => {
  it('shows required errors when submitting empty', async () => {
    render(<ContactForm />);
    fireEvent.click(screen.getByRole('button', { name: /send message/i }));
    const errs = await screen.findAllByText('This field is required');
    // fullName, email, inquiryType, subject, message
    expect(errs.length).toBeGreaterThanOrEqual(5);
  });

  it('rejects an invalid email format', async () => {
    render(<ContactForm />);
    fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: 'not-an-email' } });
    fireEvent.click(screen.getByRole('button', { name: /send message/i }));
    expect(await screen.findByText(/valid email address/i)).toBeInTheDocument();
  });

  it('rejects a too-short message', async () => {
    render(<ContactForm />);
    fireEvent.change(screen.getByLabelText(/Message/i), { target: { value: 'short' } });
    fireEvent.click(screen.getByRole('button', { name: /send message/i }));
    expect(await screen.findByText(/at least 10 characters/i)).toBeInTheDocument();
  });

  it('clears a field error when the user edits that field', async () => {
    render(<ContactForm />);
    fireEvent.click(screen.getByRole('button', { name: /send message/i }));
    await screen.findAllByText('This field is required');
    fireEvent.change(screen.getByLabelText(/Full Name/i), { target: { value: 'A' } });
    // The fullName error should be gone; others remain
    const nameInput = screen.getByLabelText(/Full Name/i);
    expect(nameInput).toHaveAttribute('aria-invalid', 'false');
  });
});

describe('submission', () => {
  it('calls onSubmit with form data and shows confirmation on success', async () => {
    const onSubmit = jest.fn().mockResolvedValue({ success: true });
    render(<ContactForm onSubmit={onSubmit} />);
    fillValid();
    fireEvent.click(screen.getByRole('button', { name: /send message/i }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ fullName: 'Ada Lovelace', email: 'ada@example.com', inquiryType: 'general-inquiry' }),
    );
    expect(await screen.findByText(/Message Sent Successfully/i)).toBeInTheDocument();
  });

  it('shows a server error message when onSubmit returns failure', async () => {
    const onSubmit = jest.fn().mockResolvedValue({ success: false, error: 'Server exploded' });
    render(<ContactForm onSubmit={onSubmit} />);
    fillValid();
    fireEvent.click(screen.getByRole('button', { name: /send message/i }));
    expect(await screen.findByText('Server exploded')).toBeInTheDocument();
  });

  it('shows a generic error when onSubmit throws', async () => {
    const onSubmit = jest.fn().mockRejectedValue(new Error('boom'));
    render(<ContactForm onSubmit={onSubmit} />);
    fillValid();
    fireEvent.click(screen.getByRole('button', { name: /send message/i }));
    expect(await screen.findByText(/unexpected error occurred/i)).toBeInTheDocument();
  });

  it('shows a helper text once an inquiry type is chosen', async () => {
    render(<ContactForm />);
    fireEvent.change(screen.getByLabelText(/Inquiry Type/i), { target: { value: 'general-inquiry' } });
    // helper text element has the describedby id
    await waitFor(() => {
      const helper = document.getElementById('contact-inquiryType-helper');
      expect(helper).toBeInTheDocument();
    });
  });
});
