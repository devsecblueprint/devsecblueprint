/**
 * Unit tests for SessionExpiryModal.
 */
import { render, screen, fireEvent, act, waitFor } from '@testing-library/react';
import { SessionExpiryModal } from '@/components/SessionExpiryModal';

beforeEach(() => jest.useFakeTimers());
afterEach(() => {
  act(() => jest.runOnlyPendingTimers());
  jest.useRealTimers();
});

function renderModal(remaining = 120, overrides: Partial<React.ComponentProps<typeof SessionExpiryModal>> = {}) {
  const onExtendSession = overrides.onExtendSession ?? jest.fn().mockResolvedValue(undefined);
  const onLogout = overrides.onLogout ?? jest.fn();
  render(
    <SessionExpiryModal
      remainingSeconds={remaining}
      onExtendSession={onExtendSession}
      onLogout={onLogout}
    />,
  );
  return { onExtendSession, onLogout };
}

it('formats the remaining time as mm:ss', () => {
  renderModal(125);
  expect(screen.getByText('02:05')).toBeInTheDocument();
});

it('counts down every second', () => {
  renderModal(120);
  expect(screen.getByText('02:00')).toBeInTheDocument();
  act(() => {
    jest.advanceTimersByTime(1000);
  });
  expect(screen.getByText('01:59')).toBeInTheDocument();
});

it('logs out automatically when time reaches zero', () => {
  const onLogout = jest.fn();
  renderModal(1, { onLogout });
  act(() => {
    jest.advanceTimersByTime(1000);
  });
  // next tick hits zero and triggers logout via the timeLeft<=0 effect
  act(() => {
    jest.advanceTimersByTime(1000);
  });
  expect(onLogout).toHaveBeenCalled();
});

it('logs out immediately if initial time is already zero', () => {
  const onLogout = jest.fn();
  renderModal(0, { onLogout });
  expect(onLogout).toHaveBeenCalled();
});

it('calls onExtendSession when Extend is clicked', async () => {
  const onExtendSession = jest.fn().mockResolvedValue(undefined);
  renderModal(120, { onExtendSession });
  fireEvent.click(screen.getByRole('button', { name: /extend session/i }));
  expect(screen.getByRole('button', { name: /extending/i })).toBeInTheDocument();
  await waitFor(() => expect(onExtendSession).toHaveBeenCalled());
});

it('re-enables the button if extend fails', async () => {
  const onExtendSession = jest.fn().mockRejectedValue(new Error('x'));
  renderModal(120, { onExtendSession });
  fireEvent.click(screen.getByRole('button', { name: /extend session/i }));
  await waitFor(() => expect(screen.getByRole('button', { name: /extend session/i })).toBeInTheDocument());
});

it('calls onLogout when Log Out is clicked', () => {
  const onLogout = jest.fn();
  renderModal(120, { onLogout });
  fireEvent.click(screen.getByRole('button', { name: /log out/i }));
  expect(onLogout).toHaveBeenCalled();
});

it('logs out on Escape key', () => {
  const onLogout = jest.fn();
  renderModal(120, { onLogout });
  fireEvent.keyDown(document, { key: 'Escape' });
  expect(onLogout).toHaveBeenCalled();
});
