/**
 * Unit tests for AuthLoadingScreen.
 */
import { render, screen } from '@testing-library/react';
import { AuthLoadingScreen } from '@/components/AuthLoadingScreen';

it('renders the default authenticating message', () => {
  render(<AuthLoadingScreen />);
  expect(screen.getByText('Authenticating...')).toBeInTheDocument();
  expect(screen.getByText(/Securing your session/i)).toBeInTheDocument();
});

it('renders a custom message', () => {
  render(<AuthLoadingScreen message="Verifying credentials..." />);
  expect(screen.getByText('Verifying credentials...')).toBeInTheDocument();
});
