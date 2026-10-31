/**
 * AdministrativeTools layout after removing the Communications and System categories.
 */
import { render, screen, within, fireEvent } from '@testing-library/react';
import { AdministrativeTools } from '@/app/admin/components/AdministrativeTools';

jest.mock('@/app/admin/components/AdminDashboardProvider', () => ({
  useAdminContext: () => ({ analytics: null }),
}));
function mockStub(testId: string) {
  const Stub = () => <div data-testid={testId} />;
  Stub.displayName = `Stub(${testId})`;
  return Stub;
}
jest.mock('@/components/admin/UserList', () => ({ UserList: mockStub('user-list') }));
jest.mock('@/components/admin/ExportData', () => ({ ExportData: mockStub('export-data') }));
jest.mock('@/components/admin/CapstoneSubmissions', () => ({ CapstoneSubmissions: mockStub('capstones') }));
jest.mock('@/components/admin/TestimonialModeration', () => ({ TestimonialModeration: mockStub('testimonials') }));
jest.mock('@/components/admin/WalkthroughStatistics', () => ({ WalkthroughStatistics: mockStub('wt-stats') }));
jest.mock('@/components/admin/WalkthroughAccessTiers', () => ({ WalkthroughAccessTiers: mockStub('wt-tiers') }));
jest.mock('@/app/admin/components/certifications/CertificationStats', () => ({ CertificationStats: mockStub('cert-stats') }));
jest.mock('@/app/admin/components/certifications/CertificationCandidates', () => ({ CertificationCandidates: mockStub('cert-candidates') }));
jest.mock('@/app/admin/components/certifications/PathwayManagement', () => ({ PathwayManagement: mockStub('pathways') }));
jest.mock('@/app/admin/components/certifications/CandidateDetailModal', () => ({ CandidateDetailModal: () => null }));
jest.mock('@/components/admin/BroadcastManagement', () => {
  throw new Error('BroadcastManagement must not be imported by AdministrativeTools');
});

it('has no Communications or System accordion items', () => {
  render(<AdministrativeTools />);
  const triggers = screen.getAllByRole('button').map((b) => b.textContent);
  expect(triggers).toEqual(expect.arrayContaining(['Member Management', 'Reviews', 'Learning & Content']));
  expect(triggers).not.toContain('Communications');
  expect(triggers).not.toContain('System');
  expect(screen.queryByText('View Active Sessions')).not.toBeInTheDocument();
  expect(document.getElementById('communications')).toBeNull();
  expect(document.getElementById('system')).toBeNull();
});

it('renders Export Data inside Member Management, after the user list', () => {
  render(<AdministrativeTools />);
  const panel = screen.getByRole('region', { name: 'Member Management' });
  const userList = within(panel).getByTestId('user-list');
  const exportData = within(panel).getByTestId('export-data');
  expect(userList.compareDocumentPosition(exportData) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
});

it('Learning & Content renders walkthrough panels but no registry/module-health panels', () => {
  render(<AdministrativeTools />);
  fireEvent.click(screen.getByRole('button', { name: 'Learning & Content' }));
  const panel = screen.getByRole('region', { name: 'Learning & Content' });
  expect(within(panel).getByTestId('wt-stats')).toBeInTheDocument();
  expect(within(panel).getByTestId('wt-tiers')).toBeInTheDocument();
  expect(within(panel).queryByText(/Content Registry Status/i)).not.toBeInTheDocument();
  expect(within(panel).queryByText(/Module Health/i)).not.toBeInTheDocument();
});
