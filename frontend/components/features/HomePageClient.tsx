'use client';

import { useState } from 'react';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { HeroSection } from '@/components/features/HeroSection';
import { HowItWorksSection } from '@/components/features/HowItWorksSection';
import { TestimonialCarousel } from '@/components/features/TestimonialCarousel';
import { GlobalMetrics } from '@/components/features/GlobalMetrics';
import { BenefitsSection } from '@/components/features/BenefitsSection';
import { BuilderJourneySection } from '@/components/features/BuilderJourneySection';
import { RegistrationCallout } from '@/components/features/RegistrationCallout';
import { FinalCTA } from '@/components/features/FinalCTA';
import { Footer } from '@/components/layout/Footer';
import { SignInModal } from '@/components/layout/SignInModal';

export function HomePageClient() {
  const [isSignInModalOpen, setIsSignInModalOpen] = useState(false);

  const handleCreateAccount = () => {
    setIsSignInModalOpen(true);
  };

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950">
      {/* Header and Navigation */}
      <NavbarWithAuth />

      {/* 1. Hero — What DSB helps me become/do */}
      <HeroSection onCreateAccount={handleCreateAccount} />

      {/* 2. How The DevSec Blueprint Works — Learn → Build → Apply → Grow */}
      <HowItWorksSection />

      {/* 3. Testimonials / Community Outcomes */}
      <TestimonialCarousel />

      {/* 4. Global Community / Platform Metrics */}
      <GlobalMetrics />

      {/* 5. What You Get — Curriculum, Walkthroughs, Projects, Community, Career */}
      <BenefitsSection />

      {/* 6. DSB Builder — Premium experience positioned after platform understanding */}
      <BuilderJourneySection />

      {/* 7. Account-Registration Callout */}
      <RegistrationCallout />

      {/* 8. Final CTA — Ready to Start Building? */}
      <FinalCTA onCreateAccount={handleCreateAccount} />

      {/* 9. Footer */}
      <Footer />

      {/* Sign In Modal */}
      <SignInModal isOpen={isSignInModalOpen} onClose={() => setIsSignInModalOpen(false)} />
    </div>
  );
}
