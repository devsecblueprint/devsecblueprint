'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { LearningPathCard } from '@/components/features/LearningPathCard';
import { Footer } from '@/components/layout/Footer';
import { LEARNING_PATHS } from '@/lib/constants';
import { SignInModal } from '@/components/layout/SignInModal';
import { TestimonialCarousel } from '@/components/features/TestimonialCarousel';

export default function Home() {
  const [isSignInModalOpen, setIsSignInModalOpen] = useState(false);

  const handleGetStarted = () => {
    setIsSignInModalOpen(true);
  };

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950">
      {/* Navbar */}
      <NavbarWithAuth />

      {/* Hero Section */}
      <section className="flex flex-col items-center justify-center px-4 sm:px-6 py-20 sm:py-24 md:py-32 pt-32">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          {/* Logo */}
          <div className="flex justify-center mb-8">
            <img 
              src="/light_mode_logo.svg" 
              alt="The DevSec Blueprint Logo" 
              className="h-48 sm:h-56 md:h-64 w-auto dark:hidden"
            />
            <img 
              src="/dark_mode_logo.svg" 
              alt="The DevSec Blueprint Logo" 
              className="h-48 sm:h-56 md:h-64 w-auto hidden dark:block"
            />
          </div>
          
          {/* Header Text */}
          <h1 className="text-lg sm:text-xl md:text-2xl font-normal text-gray-700 dark:text-gray-300 leading-relaxed max-w-3xl mx-auto">
            A comprehensive, open-source roadmap to mastering DevSecOps and Cloud Security Development. Learn the foundations, build secure systems, and gain real-world engineering experience through structured, hands-on practice.
          </h1>
          
          {/* CTA Button */}
          <div className="pt-4 flex justify-center">
            <Button 
              variant="primary" 
              size="lg"
              onClick={handleGetStarted}
              className="inline-flex items-center justify-center min-w-[200px]"
            >
              {"Let's get started!"}
            </Button>
          </div>
        </div>
      </section>

      {/* Testimonial Carousel */}
      <TestimonialCarousel />

      {/* Learning Paths Section */}
      <section className="px-4 sm:px-6 py-12 sm:py-16 md:py-24 bg-gray-50 dark:bg-gray-900/50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 dark:text-gray-100 text-center mb-8 sm:mb-12">
            Learning Paths
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 max-w-6xl mx-auto">
            {LEARNING_PATHS.map((path) => (
              <LearningPathCard key={path.id} path={path} />
            ))}
          </div>
        </div>
      </section>

      {/* Curriculum CTA Section */}
      <section className="px-4 sm:px-6 py-16 sm:py-20 bg-white dark:bg-gray-950">
        <div className="max-w-3xl mx-auto text-center">
          <p className="text-lg sm:text-xl text-gray-700 dark:text-gray-300 mb-8">
            Interested in the curriculum? Click the button below
          </p>
          <a
            href="/curriculum"
            className="inline-flex items-center justify-center px-8 py-4 text-lg font-semibold text-gray-900 bg-primary-400 hover:bg-primary-500 rounded-lg transition-colors shadow-lg hover:shadow-xl"
          >
            View Full Curriculum
          </a>
        </div>
      </section>

      {/* Footer */}
      <Footer />

      {/* Sign In Modal */}
      <SignInModal isOpen={isSignInModalOpen} onClose={() => setIsSignInModalOpen(false)} />
    </div>
  );
}
