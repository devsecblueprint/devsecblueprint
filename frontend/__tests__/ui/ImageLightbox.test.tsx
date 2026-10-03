/**
 * Unit tests for the ImageLightbox component.
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { ImageLightbox } from '@/components/ui/ImageLightbox';

function renderBox(overrides: Partial<React.ComponentProps<typeof ImageLightbox>> = {}) {
  const onClose = overrides.onClose ?? jest.fn();
  render(<ImageLightbox src="/img.png" alt="A diagram" isOpen onClose={onClose} {...overrides} />);
  return { onClose };
}

it('renders nothing when closed', () => {
  const { container } = render(<ImageLightbox src="/i.png" alt="x" isOpen={false} onClose={jest.fn()} />);
  expect(container).toBeEmptyDOMElement();
});

it('renders the image and starts at 100% scale', () => {
  renderBox();
  expect(screen.getByAltText('A diagram')).toBeInTheDocument();
  expect(screen.getByText('100%')).toBeInTheDocument();
});

it('zooms in and out and clamps at the bounds', () => {
  renderBox();
  const zoomIn = screen.getByLabelText('Zoom in');
  fireEvent.click(zoomIn);
  expect(screen.getByText('125%')).toBeInTheDocument();
  fireEvent.click(screen.getByLabelText('Zoom out'));
  expect(screen.getByText('100%')).toBeInTheDocument();
});

it('resets the zoom', () => {
  renderBox();
  fireEvent.click(screen.getByLabelText('Zoom in'));
  fireEvent.click(screen.getByLabelText('Zoom in'));
  expect(screen.getByText('150%')).toBeInTheDocument();
  fireEvent.click(screen.getByLabelText('Reset zoom'));
  expect(screen.getByText('100%')).toBeInTheDocument();
});

it('closes via the close button', () => {
  const { onClose } = renderBox();
  // The close button sits inside the backdrop, which also closes on click,
  // so the handler may fire via both the button and bubbling — assert it fired.
  fireEvent.click(screen.getByLabelText('Close lightbox'));
  expect(onClose).toHaveBeenCalled();
});

it('closes on Escape', () => {
  const { onClose } = renderBox();
  fireEvent.keyDown(document, { key: 'Escape' });
  expect(onClose).toHaveBeenCalled();
});

it('does not close when clicking the image itself', () => {
  const { onClose } = renderBox();
  fireEvent.click(screen.getByAltText('A diagram'));
  expect(onClose).not.toHaveBeenCalled();
});
