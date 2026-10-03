/**
 * Unit tests for CourseContentRenderer.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { CourseContentRenderer } from '@/components/CourseContentRenderer';

jest.mock('@/components/ui/ImageLightbox', () => ({
  ImageLightbox: ({ isOpen, src }: { isOpen: boolean; src: string }) =>
    isOpen ? <div data-testid="lightbox" data-src={src} /> : null,
}));

it('renders provided HTML content', () => {
  const { container } = render(<CourseContentRenderer html="<h2>Lesson</h2><p>Body text</p>" />);
  expect(container.querySelector('h2')?.textContent).toBe('Lesson');
  expect(screen.getByText('Body text')).toBeInTheDocument();
});

it('opens the lightbox when an image in the content is clicked', async () => {
  const { container } = render(
    <CourseContentRenderer html='<img src="/diagram.png" alt="Arch diagram" />' />,
  );
  const img = container.querySelector('img')!;
  fireEvent.click(img);
  await waitFor(() => expect(screen.getByTestId('lightbox')).toBeInTheDocument());
  expect(screen.getByTestId('lightbox')).toHaveAttribute('data-src', expect.stringContaining('/diagram.png'));
});

it('does not render a lightbox before any image click', () => {
  render(<CourseContentRenderer html="<p>No images here</p>" />);
  expect(screen.queryByTestId('lightbox')).not.toBeInTheDocument();
});
