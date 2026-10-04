/**
 * Unit tests for ContactFormWithSubmit.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { ContactFormWithSubmit } from '@/components/features/ContactFormWithSubmit';

jest.mock('@/lib/api', () => ({ apiClient: { post: jest.fn() } }));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function fillValidForm() {
  fireEvent.change(screen.getByLabelText(/Full Name/i), { target: { value: 'Ada Lovelace' } });
  fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: 'ada@example.com' } });
  fireEvent.change(screen.getByLabelText(/Inquiry Type/i), { target: { value: 'general-inquiry' } });
  fireEvent.change(screen.getByLabelText(/Subject/i), { target: { value: 'Hi' } });
  fireEvent.change(screen.getByLabelText(/Message/i), { target: { value: 'This is a long enough message.' } });
}

beforeEach(() => jest.clearAllMocks());

it('submits to the contact API and shows the success modal', async () => {
  mockApi.post.mockResolvedValue({ data: { success: true, message: 'ok' }, statusCode: 200 });
  render(<ContactFormWithSubmit />);
  fillValidForm();
  fireEvent.click(screen.getByRole('button', { name: /send message/i }));

  await waitFor(() => expect(mockApi.post).toHaveBeenCalledWith('/api/contact', expect.objectContaining({
    full_name: 'Ada Lovelace',
    email: 'ada@example.com',
    inquiry_type: 'general-inquiry',
  })));
  expect(await screen.findByText('Message Sent!')).toBeInTheDocument();
});

it('shows a server error inline when the API returns an error', async () => {
  mockApi.post.mockResolvedValue({ error: 'rate limited', statusCode: 429 });
  render(<ContactFormWithSubmit />);
  fillValidForm();
  fireEvent.click(screen.getByRole('button', { name: /send message/i }));
  expect(await screen.findByText('rate limited')).toBeInTheDocument();
  expect(screen.queryByText('Message Sent!')).not.toBeInTheDocument();
});

it('closes the success modal and resets the form', async () => {
  mockApi.post.mockResolvedValue({ data: { success: true, message: 'ok' }, statusCode: 200 });
  render(<ContactFormWithSubmit />);
  fillValidForm();
  fireEvent.click(screen.getByRole('button', { name: /send message/i }));
  await screen.findByText('Message Sent!');
  fireEvent.click(screen.getByRole('button', { name: /got it/i }));
  await waitFor(() => expect(screen.queryByText('Message Sent!')).not.toBeInTheDocument());
  // Form is back (remounted) with an empty full name
  expect((screen.getByLabelText(/Full Name/i) as HTMLInputElement).value).toBe('');
});

it('closes the success modal on Escape', async () => {
  mockApi.post.mockResolvedValue({ data: { success: true, message: 'ok' }, statusCode: 200 });
  render(<ContactFormWithSubmit />);
  fillValidForm();
  fireEvent.click(screen.getByRole('button', { name: /send message/i }));
  await screen.findByText('Message Sent!');
  fireEvent.keyDown(document, { key: 'Escape' });
  await waitFor(() => expect(screen.queryByText('Message Sent!')).not.toBeInTheDocument());
});
