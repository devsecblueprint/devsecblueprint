/**
 * Unit tests for BadgeNotification.
 */
import { render, screen, fireEvent, act } from '@testing-library/react';
import { BadgeNotification } from '@/components/BadgeNotification';

const badge = { id: 'b1', title: 'First Steps', description: 'Complete your first lesson', icon: '🎯', earned: true };

beforeEach(() => jest.useFakeTimers());
afterEach(() => {
  act(() => jest.runOnlyPendingTimers());
  jest.useRealTimers();
});

it('renders the earned badge content', () => {
  render(<BadgeNotification badge={badge as never} onClose={jest.fn()} />);
  expect(screen.getByText('Badge Earned!')).toBeInTheDocument();
  expect(screen.getByText('First Steps')).toBeInTheDocument();
  expect(screen.getByText('Complete your first lesson')).toBeInTheDocument();
});

it('closes when the close button is clicked (after exit animation)', () => {
  const onClose = jest.fn();
  render(<BadgeNotification badge={badge as never} onClose={onClose} />);
  fireEvent.click(screen.getByLabelText('Close notification'));
  act(() => {
    jest.advanceTimersByTime(300);
  });
  expect(onClose).toHaveBeenCalled();
});

it('auto-dismisses after the timeout', () => {
  const onClose = jest.fn();
  render(<BadgeNotification badge={badge as never} onClose={onClose} />);
  act(() => {
    jest.advanceTimersByTime(3000); // auto-dismiss triggers handleClose
    jest.advanceTimersByTime(300); // exit animation completes
  });
  expect(onClose).toHaveBeenCalled();
});
