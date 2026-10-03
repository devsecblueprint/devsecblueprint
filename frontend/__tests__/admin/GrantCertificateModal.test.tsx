/**
 * Unit tests for GrantCertificateModal.
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { GrantCertificateModal } from '@/components/admin/GrantCertificateModal';

function renderModal(props: Partial<React.ComponentProps<typeof GrantCertificateModal>> = {}) {
  const onConfirm = props.onConfirm ?? jest.fn();
  const onClose = props.onClose ?? jest.fn();
  render(
    <GrantCertificateModal username="ada" capstoneName="DevSecOps Capstone" onConfirm={onConfirm} onClose={onClose} {...props} />,
  );
  return { onConfirm, onClose };
}

it('renders the grant confirmation with username and capstone', () => {
  renderModal();
  expect(screen.getByRole('heading', { name: 'Grant Certificate' })).toBeInTheDocument();
  expect(screen.getByText('ada')).toBeInTheDocument();
  expect(screen.getByText('DevSecOps Capstone')).toBeInTheDocument();
});

it('confirms the grant', () => {
  const { onConfirm } = renderModal();
  fireEvent.click(screen.getByRole('button', { name: /^grant certificate$/i }));
  expect(onConfirm).toHaveBeenCalled();
});

it('cancels via the Cancel button', () => {
  const { onClose } = renderModal();
  fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
  expect(onClose).toHaveBeenCalled();
});

it('closes on Escape', () => {
  const { onClose } = renderModal();
  fireEvent.keyDown(document, { key: 'Escape' });
  expect(onClose).toHaveBeenCalled();
});

it('shows a granting state and disables actions', () => {
  const { onClose } = renderModal({ isGranting: true });
  expect(screen.getByText('Granting...')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /cancel/i })).toBeDisabled();
  // Escape is ignored while granting
  fireEvent.keyDown(document, { key: 'Escape' });
  expect(onClose).not.toHaveBeenCalled();
});
