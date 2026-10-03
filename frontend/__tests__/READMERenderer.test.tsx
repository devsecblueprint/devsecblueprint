/**
 * Unit tests for READMERenderer — exercises the remark/rehype pipeline,
 * admonition conversion, image path resolution, and lightbox wiring.
 */
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { READMERenderer } from '@/components/READMERenderer';

// Keep the lightbox simple and observable.
jest.mock('@/components/ui/ImageLightbox', () => ({
  ImageLightbox: ({ isOpen, src }: { isOpen: boolean; src: string }) =>
    isOpen ? <div data-testid="lightbox" data-src={src} /> : null,
}));

function renderReadme(markdown: string, id = 'my-walkthrough') {
  return render(<READMERenderer markdown={markdown} walkthroughId={id} />);
}

it('shows a loading state then renders processed HTML', async () => {
  renderReadme('# Hello World');
  expect(screen.getByText(/Loading README/i)).toBeInTheDocument();
  await waitFor(() => expect(screen.getByText('Hello World')).toBeInTheDocument());
});

it('renders basic markdown elements', async () => {
  const { container } = renderReadme('## Section\n\nSome **bold** text.');
  await waitFor(() => expect(container.querySelector('h2')).toBeInTheDocument());
  expect(container.querySelector('strong')?.textContent).toBe('bold');
});

it('resolves relative image paths under the walkthrough public dir', async () => {
  const { container } = renderReadme('![diagram](./images/arch.png)', 'wt-1');
  await waitFor(() => expect(container.querySelector('img')).toBeInTheDocument());
  const img = container.querySelector('img')!;
  expect(img.getAttribute('src')).toBe('/walkthroughs/wt-1/images/arch.png');
});

it('leaves absolute image URLs untouched', async () => {
  const { container } = renderReadme('![x](https://cdn.example.com/a.png)');
  await waitFor(() => expect(container.querySelector('img')).toBeInTheDocument());
  expect(container.querySelector('img')!.getAttribute('src')).toBe('https://cdn.example.com/a.png');
});

it('adds default alt text to images missing it', async () => {
  const { container } = renderReadme('![](./x.png)');
  await waitFor(() => expect(container.querySelector('img')).toBeInTheDocument());
  expect(container.querySelector('img')!.getAttribute('alt')).toBe('Image from walkthrough documentation');
});

it('converts a :::note directive into an admonition', async () => {
  const { container } = renderReadme(':::note\nBe careful here.\n:::');
  await waitFor(() => expect(container.querySelector('.admonition')).toBeInTheDocument());
  expect(container.querySelector('.admonition-note')).toBeInTheDocument();
});

it('renders a plain blockquote when no alert marker is present', async () => {
  const { container } = renderReadme('> Just a normal quote.');
  await waitFor(() => expect(container.querySelector('blockquote')).toBeInTheDocument());
});

it('opens the lightbox when a rendered image is clicked', async () => {
  const { container } = renderReadme('![pic](./p.png)', 'wt-9');
  await waitFor(() => expect(container.querySelector('img')).toBeInTheDocument());
  fireEvent.click(container.querySelector('img')!);
  await waitFor(() => expect(screen.getByTestId('lightbox')).toBeInTheDocument());
});
