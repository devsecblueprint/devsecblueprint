/**
 * Unit tests for HomePageClient composition + sign-in modal wiring.
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { HomePageClient } from '@/components/features/HomePageClient';

// Mock all section children so we test composition + modal state only.
jest.mock('@/components/layout/NavbarWithAuth', () => ({ NavbarWithAuth: () => <nav data-testid="navbar" /> }));
jest.mock('@/components/features/HeroSection', () => ({
  HeroSection: ({ onCreateAccount }: { onCreateAccount: () => void }) => (
    <button onClick={onCreateAccount}>hero-create-account</button>
  ),
}));
jest.mock('@/components/features/HowItWorksSection', () => ({ HowItWorksSection: () => <div /> }));
jest.mock('@/components/features/CompanyCarousel', () => ({ CompanyCarousel: () => <div /> }));
jest.mock('@/components/features/TestimonialCarousel', () => ({ TestimonialCarousel: () => <div /> }));
jest.mock('@/components/features/GlobalMetrics', () => ({ GlobalMetrics: () => <div /> }));
jest.mock('@/components/features/BenefitsSection', () => ({ BenefitsSection: () => <div /> }));
jest.mock('@/components/features/BuilderJourneySection', () => ({ BuilderJourneySection: () => <div /> }));
jest.mock('@/components/features/RegistrationCallout', () => ({ RegistrationCallout: () => <div /> }));
jest.mock('@/components/features/FinalCTA', () => ({
  FinalCTA: ({ onCreateAccount }: { onCreateAccount: () => void }) => (
    <button onClick={onCreateAccount}>final-create-account</button>
  ),
}));
jest.mock('@/components/layout/Footer', () => ({ Footer: () => <footer /> }));
jest.mock('@/components/layout/SignInModal', () => ({
  SignInModal: ({ isOpen }: { isOpen: boolean }) => (isOpen ? <div data-testid="signin-modal" /> : null),
}));

it('renders the page composition with the navbar', () => {
  render(<HomePageClient />);
  expect(screen.getByTestId('navbar')).toBeInTheDocument();
});

it('opens the sign-in modal from the hero create-account action', () => {
  render(<HomePageClient />);
  expect(screen.queryByTestId('signin-modal')).not.toBeInTheDocument();
  fireEvent.click(screen.getByText('hero-create-account'));
  expect(screen.getByTestId('signin-modal')).toBeInTheDocument();
});

it('opens the sign-in modal from the final CTA', () => {
  render(<HomePageClient />);
  fireEvent.click(screen.getByText('final-create-account'));
  expect(screen.getByTestId('signin-modal')).toBeInTheDocument();
});
