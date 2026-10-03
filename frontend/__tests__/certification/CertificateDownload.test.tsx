/**
 * Unit tests for CertificateDownload.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { CertificateDownload } from '@/app/components/certification/CertificateDownload';

jest.mock('@/lib/api', () => ({ apiClient: { get: jest.fn() } }));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

beforeEach(() => {
  jest.clearAllMocks();
  jest.spyOn(window, 'open').mockImplementation(() => null);
});

it('renders an enabled download button', () => {
  render(<CertificateDownload pathway_id="devsecops" disabled={false} />);
  expect(screen.getByRole('button', { name: /download certificate pdf/i })).toBeEnabled();
});

it('is disabled when the certificate is not generated', () => {
  render(<CertificateDownload pathway_id="devsecops" disabled />);
  expect(screen.getByRole('button', { name: /download unavailable/i })).toBeDisabled();
});

it('opens the download URL on success', async () => {
  mockApi.get.mockResolvedValue({ data: { download_url: 'https://cdn/cert.pdf' }, statusCode: 200 });
  render(<CertificateDownload pathway_id="devsecops" disabled={false} />);
  fireEvent.click(screen.getByRole('button', { name: /download certificate pdf/i }));
  await waitFor(() => expect(window.open).toHaveBeenCalledWith('https://cdn/cert.pdf', '_blank', 'noopener,noreferrer'));
});

it('shows an error when the request fails', async () => {
  mockApi.get.mockResolvedValue({ error: 'not ready', statusCode: 404 });
  render(<CertificateDownload pathway_id="devsecops" disabled={false} />);
  fireEvent.click(screen.getByRole('button', { name: /download certificate pdf/i }));
  expect(await screen.findByRole('alert')).toHaveTextContent('not ready');
});

it('shows a generic error when the fetch throws', async () => {
  mockApi.get.mockRejectedValue(new Error('network'));
  render(<CertificateDownload pathway_id="devsecops" disabled={false} />);
  fireEvent.click(screen.getByRole('button', { name: /download certificate pdf/i }));
  expect(await screen.findByText(/Failed to fetch download URL/i)).toBeInTheDocument();
});
