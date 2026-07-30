'use client';

import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { Footer } from '@/components/layout/Footer';
import { CurriculumHero } from '@/components/features/curriculum/CurriculumHero';
import { CurriculumStages } from '@/components/features/curriculum/CurriculumStages';

export default function CurriculumPage() {
  return (
    <div className="min-h-screen bg-white dark:bg-gray-950">
      <NavbarWithAuth />
      <main className="pt-16">
        <CurriculumHero />
        <div className="bg-gray-50 dark:bg-gray-900/50">
          <CurriculumStages />
        </div>
      </main>
      <Footer />
    </div>
  );
}
