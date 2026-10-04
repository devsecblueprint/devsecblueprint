/**
 * Unit tests for CertificationsDashboardWidget.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { CertificationsDashboardWidget } from '@/components/dashboard/CertificationsDashboardWidget';

jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
}));
jest.mock('@/lib/api', () => ({ apiClient: { get: jest.fn() } }));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function pathway(id: string, status: string) {
  return { pathway_id: id, display_name: `Pathway ${id}`, candidate_status: status };
}

beforeEach(() => jest.clearAllMocks());

it('renders nothing while loading', () => {
  mockApi.get.mockReturnValue(new Promise(() => {}));
  const { container } = render(<CertificationsDashboardWidget />);
  expect(container).toBeEmptyDOMElement();
});

it('shows a get-started prompt when there is no activity', async () => {
  mockApi.get.mockResolvedValue({ data: [pathway('p1', 'NOT_STARTED')] as never, statusCode: 200 });
  render(<CertificationsDashboardWidget />);
  expect(await screen.findByText('DSB Certifications')).toBeInTheDocument();
  expect(screen.getByText(/Get Started/i)).toBeInTheDocument();
});

it('lists awarded and in-progress certifications', async () => {
  mockApi.get.mockResolvedValue({
    data: [pathway('p1', 'AWARDED'), pathway('p2', 'IN_PROGRESS')] as never,
    statusCode: 200,
  });
  render(<CertificationsDashboardWidget />);
  expect(await screen.findByText('Pathway p1')).toBeInTheDocument();
  expect(screen.getByText('Active')).toBeInTheDocument();
  expect(screen.getByText('Pathway p2')).toBeInTheDocument();
  expect(screen.getByText('In Progress')).toBeInTheDocument();
});

it('silently renders nothing-meaningful when the fetch throws', async () => {
  mockApi.get.mockRejectedValue(new Error('boom'));
  render(<CertificationsDashboardWidget />);
  // After a failed fetch with no data, it falls to the empty prompt
  expect(await screen.findByText('DSB Certifications')).toBeInTheDocument();
});
