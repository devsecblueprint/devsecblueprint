/**
 * Unit tests for NotificationDropdown.
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { NotificationDropdown } from '@/components/layout/NotificationDropdown';

function note(id: string, overrides: Record<string, unknown> = {}) {
  return {
    notification_id: id,
    message: `Message ${id}`,
    link: `/go/${id}`,
    created_at: new Date().toISOString(),
    ...overrides,
  };
}

beforeEach(() => jest.clearAllMocks());

it('shows an empty state', () => {
  render(<NotificationDropdown notifications={[]} onAcknowledge={jest.fn()} onClose={jest.fn()} />);
  expect(screen.getByText('No notifications yet')).toBeInTheDocument();
});

it('renders notifications and acknowledges on click', () => {
  const onAcknowledge = jest.fn();
  render(
    <NotificationDropdown notifications={[note('1'), note('2')]} onAcknowledge={onAcknowledge} onClose={jest.fn()} />,
  );
  expect(screen.getByText('Message 1')).toBeInTheDocument();
  fireEvent.click(screen.getByText('Message 2'));
  expect(onAcknowledge).toHaveBeenCalledWith('2', '/go/2');
});

it('formats relative timestamps', () => {
  render(
    <NotificationDropdown
      notifications={[note('1', { created_at: new Date(Date.now() - 2 * 3600000).toISOString() })]}
      onAcknowledge={jest.fn()}
      onClose={jest.fn()}
    />,
  );
  expect(screen.getByText('2h ago')).toBeInTheDocument();
});

it('navigates items with arrow keys', () => {
  render(
    <NotificationDropdown notifications={[note('1'), note('2')]} onAcknowledge={jest.fn()} onClose={jest.fn()} />,
  );
  const items = screen.getAllByRole('menuitem');
  // First item is focused on mount
  expect(items[0]).toHaveFocus();
  fireEvent.keyDown(screen.getByRole('menu'), { key: 'ArrowDown' });
  expect(items[1]).toHaveFocus();
  fireEvent.keyDown(screen.getByRole('menu'), { key: 'ArrowUp' });
  expect(items[0]).toHaveFocus();
});

it('closes on Escape', () => {
  const onClose = jest.fn();
  render(<NotificationDropdown notifications={[note('1')]} onAcknowledge={jest.fn()} onClose={onClose} />);
  fireEvent.keyDown(screen.getByRole('menu'), { key: 'Escape' });
  expect(onClose).toHaveBeenCalled();
});

it('closes on outside click', () => {
  const onClose = jest.fn();
  render(
    <div>
      <button>outside</button>
      <NotificationDropdown notifications={[note('1')]} onAcknowledge={jest.fn()} onClose={onClose} />
    </div>,
  );
  fireEvent.mouseDown(screen.getByText('outside'));
  expect(onClose).toHaveBeenCalled();
});
