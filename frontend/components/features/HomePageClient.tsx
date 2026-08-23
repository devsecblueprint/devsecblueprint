'use client';

import { useState } from 'react';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { HeroSection } from '@/components/features/HeroSection';
import { HowItWorksSection } from '@/components/features/HowItWorksSection';
import { CompanyCarousel } from '@/components/features/CompanyCarousel';
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

      {/* 3. Companies Where DSB Members Have Landed */}
      <CompanyCarousel />

      {/* 4. Testimonials / Community Outcomes */}
      <TestimonialCarousel />

      {/* 5. Global Community / Platform Metrics */}
      <GlobalMetrics />

      {/* 6. What You Get — Curriculum, Walkthroughs, Projects, Community, Career */}
      <BenefitsSection />

      {/* 7. DSB Builder — Premium experience positioned after platform understanding */}
      <BuilderJourneySection />

      {/* 8. Account-Registration Callout */}
      <RegistrationCallout />

      {/* 9. Final CTA — Ready to Start Building? */}
      <FinalCTA onCreateAccount={handleCreateAccount} />

      {/* 10. Footer */}
      <Footer />

      {/* Sign In Modal */}
      <SignInModal isOpen={isSignInModalOpen} onClose={() => setIsSignInModalOpen(false)} />
    </div>
  );
}
