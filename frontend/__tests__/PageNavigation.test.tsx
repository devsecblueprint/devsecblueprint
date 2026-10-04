/**
 * Unit tests for PageNavigation.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { PageNavigation } from '@/components/PageNavigation';

const pushMock = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: pushMock }),
  usePathname: () => '/learn/page-1',
}));
jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href, onClick }: { children: React.ReactNode; href: string; onClick?: (e: React.MouseEvent) => void }) => (
    <a href={href} onClick={onClick}>{children}</a>
  ),
}));

beforeEach(() => {
  jest.clearAllMocks();
  // @ts-expect-error cleanup global
  delete (window as any).__markPageComplete;
});

it('renders the section position', () => {
  render(<PageNavigation previousUrl="/a" nextUrl="/b" currentPosition={2} totalSections={5} />);
  expect(screen.getByText('Section 2 of 5')).toBeInTheDocument();
});

it('navigates to the previous page', () => {
  render(<PageNavigation previousUrl="/a" nextUrl="/b" currentPosition={2} totalSections={5} />);
  fireEvent.click(screen.getByText('Previous'));
  expect(pushMock).toHaveBeenCalledWith('/a');
});

it('marks the page complete then navigates on Next', async () => {
  const markComplete = jest.fn().mockResolvedValue(undefined);
  (window as any).__markPageComplete = markComplete;
  render(<PageNavigation previousUrl="/a" nextUrl="/b" currentPosition={2} totalSections={5} />);
  fireEvent.click(screen.getByText('Next'));
  await waitFor(() => expect(markComplete).toHaveBeenCalled());
  await waitFor(() => expect(pushMock).toHaveBeenCalledWith('/b'));
});

it('still navigates when the save fails', async () => {
  (window as any).__markPageComplete = jest.fn().mockRejectedValue(new Error('save failed'));
  const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
  render(<PageNavigation previousUrl={null} nextUrl="/b" currentPosition={1} totalSections={5} />);
  fireEvent.click(screen.getByText('Next'));
  await waitFor(() => expect(pushMock).toHaveBeenCalledWith('/b'));
  spy.mockRestore();
});

it('omits the Previous link on the first section', () => {
  render(<PageNavigation previousUrl={null} nextUrl="/b" currentPosition={1} totalSections={5} />);
  expect(screen.queryByText('Previous')).not.toBeInTheDocument();
  expect(screen.getByText('Next')).toBeInTheDocument();
});

it('omits the Next link on the last section', () => {
  render(<PageNavigation previousUrl="/a" nextUrl={null} currentPosition={5} totalSections={5} />);
  expect(screen.queryByText('Next')).not.toBeInTheDocument();
  expect(screen.getByText('Previous')).toBeInTheDocument();
});
