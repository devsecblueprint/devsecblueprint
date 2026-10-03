/**
 * Unit tests for RevokeCredentialModal.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { RevokeCredentialModal } from '@/app/admin/components/certifications/RevokeCredentialModal';

jest.mock('@/lib/api', () => ({ apiClient: { post: jest.fn() } }));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function renderModal(props: Partial<React.ComponentProps<typeof RevokeCredentialModal>> = {}) {
  const onClose = props.onClose ?? jest.fn();
  const onRevoked = props.onRevoked ?? jest.fn();
  render(
    <RevokeCredentialModal
      isOpen
      onClose={onClose}
      credentialId="CRED-1"
      holderName="Ada"
      pathwayName="DevSecOps"
      onRevoked={onRevoked}
      {...props}
    />,
  );
  return { onClose, onRevoked };
}

beforeEach(() => jest.clearAllMocks());

it('renders nothing when closed', () => {
  const { container } = render(
    <RevokeCredentialModal isOpen={false} onClose={jest.fn()} credentialId="C" holderName="A" pathwayName="P" onRevoked={jest.fn()} />,
  );
  expect(container).toBeEmptyDOMElement();
});

it('renders the credential summary', () => {
  renderModal();
  expect(screen.getByText('CRED-1')).toBeInTheDocument();
  expect(screen.getByText('Ada')).toBeInTheDocument();
  expect(screen.getByText('DevSecOps')).toBeInTheDocument();
});

it('keeps the revoke button disabled until a valid reason is entered', () => {
  renderModal();
  const confirm = screen.getByRole('button', { name: /confirm credential revocation/i });
  expect(confirm).toBeDisabled();
  fireEvent.change(screen.getByLabelText(/Revocation Reason/i), { target: { value: 'bad' } });
  expect(confirm).toBeDisabled();
  fireEvent.change(screen.getByLabelText(/Revocation Reason/i), { target: { value: 'violation of terms' } });
  expect(confirm).toBeEnabled();
});

it('revokes with a valid reason', async () => {
  mockApi.post.mockResolvedValue({ data: {} as never, statusCode: 200 });
  const { onRevoked } = renderModal();
  fireEvent.change(screen.getByLabelText(/Revocation Reason/i), { target: { value: 'violation of terms' } });
  fireEvent.click(screen.getByRole('button', { name: /confirm credential revocation/i }));
  await waitFor(() => expect(mockApi.post).toHaveBeenCalledWith('/admin/certifications/credentials/CRED-1/revoke', { reason: 'violation of terms' }));
  expect(onRevoked).toHaveBeenCalled();
});

it('surfaces a revoke error', async () => {
  mockApi.post.mockResolvedValue({ error: 'cannot revoke', statusCode: 500 });
  renderModal();
  fireEvent.change(screen.getByLabelText(/Revocation Reason/i), { target: { value: 'violation of terms' } });
  fireEvent.click(screen.getByRole('button', { name: /confirm credential revocation/i }));
  expect(await screen.findByText('cannot revoke')).toBeInTheDocument();
});

it('cancels and clears via the Cancel button', () => {
  const { onClose } = renderModal();
  fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
  expect(onClose).toHaveBeenCalled();
});
