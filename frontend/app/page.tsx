'use client';

import { useState } from 'react';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { HeroSection } from '@/components/features/HeroSection';
import { TestimonialCarousel } from '@/components/features/TestimonialCarousel';
import { GlobalMetrics } from '@/components/features/GlobalMetrics';
import { BenefitsSection } from '@/components/features/BenefitsSection';
import { RegistrationCallout } from '@/components/features/RegistrationCallout';
import { FinalCTA } from '@/components/features/FinalCTA';
import { Footer } from '@/components/layout/Footer';
import { SignInModal } from '@/components/layout/SignInModal';

export default function Home() {
  const [isSignInModalOpen, setIsSignInModalOpen] = useState(false);

  const handleCreateAccount = () => {
    setIsSignInModalOpen(true);
  };

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950">
      {/* Header and Navigation */}
      <NavbarWithAuth />

      {/* 1. Hero */}
      <HeroSection onCreateAccount={handleCreateAccount} />

      {/* 2. Learner Testimonials */}
      <TestimonialCarousel />

      {/* 3. Global Community Metrics */}
      <GlobalMetrics />

      {/* 4. What Users Receive */}
      <BenefitsSection />

      {/* 5. Account-Registration Callout */}
      <RegistrationCallout onCreateAccount={handleCreateAccount} />

      {/* 6. Final CTA */}
      <FinalCTA onCreateAccount={handleCreateAccount} />

      {/* 7. Footer */}
      <Footer />

      {/* Sign In Modal */}
      <SignInModal isOpen={isSignInModalOpen} onClose={() => setIsSignInModalOpen(false)} />
    </div>
  );
}
