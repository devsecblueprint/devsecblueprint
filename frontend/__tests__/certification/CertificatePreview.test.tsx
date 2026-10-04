/**
 * Unit tests for CertificatePreview.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { CertificatePreview } from '@/app/components/certification/CertificatePreview';

const mockFetch = jest.fn();
global.fetch = mockFetch;

beforeEach(() => {
  jest.clearAllMocks();
  global.URL.createObjectURL = jest.fn(() => 'blob:cert');
  global.URL.revokeObjectURL = jest.fn();
});

it('shows a loading placeholder initially', () => {
  mockFetch.mockReturnValue(new Promise(() => {}));
  render(<CertificatePreview pathwayId="devsecops" />);
  expect(screen.getByText(/Loading certificate preview/i)).toBeInTheDocument();
});

it('renders the certificate image on success', async () => {
  mockFetch.mockResolvedValue({ ok: true, blob: () => Promise.resolve(new Blob(['<svg/>'])) });
  render(<CertificatePreview pathwayId="devsecops" />);
  const img = await screen.findByAltText('Certificate of Achievement');
  expect(img).toHaveAttribute('src', 'blob:cert');
});

it('shows an unavailable message when the request fails', async () => {
  mockFetch.mockResolvedValue({ ok: false });
  render(<CertificatePreview pathwayId="devsecops" />);
  expect(await screen.findByText(/Certificate preview unavailable/i)).toBeInTheDocument();
});

it('shows an unavailable message when fetch throws', async () => {
  mockFetch.mockRejectedValue(new Error('network'));
  render(<CertificatePreview pathwayId="devsecops" />);
  expect(await screen.findByText(/Certificate preview unavailable/i)).toBeInTheDocument();
});
