/**
 * Unit tests for the admin FeedbackModal.
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { FeedbackModal } from '@/components/admin/FeedbackModal';

jest.mock('@/components/MarkdownRenderer', () => ({
  __esModule: true,
  default: ({ markdown }: { markdown: string }) => <div data-testid="md">{markdown}</div>,
}));

function renderModal(overrides: Partial<React.ComponentProps<typeof FeedbackModal>> = {}) {
  const onSubmit = overrides.onSubmit ?? jest.fn();
  const onClose = overrides.onClose ?? jest.fn();
  render(
    <FeedbackModal
      username="ada"
      contentId="capstone-1"
      onSubmit={onSubmit}
      onClose={onClose}
      {...overrides}
    />,
  );
  return { onSubmit, onClose };
}

it('renders the header with username and content id', () => {
  renderModal();
  expect(screen.getByText('Review Capstone Submission')).toBeInTheDocument();
  expect(screen.getByText('ada — capstone-1')).toBeInTheDocument();
});

it('validates that feedback is required', () => {
  const { onSubmit } = renderModal();
  fireEvent.click(screen.getByRole('button', { name: /submit review/i }));
  expect(screen.getByText(/Feedback is required/i)).toBeInTheDocument();
  expect(onSubmit).not.toHaveBeenCalled();
});

it('submits trimmed feedback', () => {
  const { onSubmit } = renderModal();
  fireEvent.change(screen.getByLabelText(/Feedback markdown editor/i), { target: { value: '  great work  ' } });
  fireEvent.click(screen.getByRole('button', { name: /submit review/i }));
  expect(onSubmit).toHaveBeenCalledWith('great work', undefined);
});

it('toggles to preview mode and renders markdown', () => {
  renderModal();
  fireEvent.change(screen.getByLabelText(/Feedback markdown editor/i), { target: { value: '# Heading' } });
  fireEvent.click(screen.getByRole('button', { name: /^preview$/i }));
  expect(screen.getByTestId('md')).toHaveTextContent('# Heading');
});

it('shows an empty-preview hint when there is no feedback', () => {
  renderModal();
  fireEvent.click(screen.getByRole('button', { name: /^preview$/i }));
  expect(screen.getByText(/Nothing to preview yet/i)).toBeInTheDocument();
});

it('requires a grade when certification grading is enabled', () => {
  const { onSubmit } = renderModal({ showCertificationGrade: true });
  fireEvent.change(screen.getByLabelText(/Feedback markdown editor/i), { target: { value: 'good' } });
  fireEvent.click(screen.getByRole('button', { name: /submit/i }));
  expect(screen.getByText(/select a certification grade/i)).toBeInTheDocument();
  expect(onSubmit).not.toHaveBeenCalled();
});

it('submits with the selected grade', () => {
  const { onSubmit } = renderModal({ showCertificationGrade: true });
  fireEvent.change(screen.getByLabelText(/Feedback markdown editor/i), { target: { value: 'excellent' } });
  fireEvent.click(screen.getByRole('button', { name: /pass/i }));
  fireEvent.click(screen.getByRole('button', { name: /submit & grant credential/i }));
  expect(onSubmit).toHaveBeenCalledWith('excellent', 'PASS');
});

it('closes via the Cancel button', () => {
  const { onClose } = renderModal();
  fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
  expect(onClose).toHaveBeenCalled();
});

it('closes on Escape', () => {
  const { onClose } = renderModal();
  fireEvent.keyDown(document, { key: 'Escape' });
  expect(onClose).toHaveBeenCalled();
});
