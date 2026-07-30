import Link from 'next/link';
import { Button } from '@/components/ui/Button';

export function CurriculumHero() {
  return (
    <section className="px-4 sm:px-6 py-16 sm:py-20 md:py-24">
      <div className="max-w-4xl mx-auto text-center">
        <p className="text-sm font-semibold uppercase tracking-wider text-primary-500 dark:text-primary-400 mb-4">
          STRUCTURED LEARNING PATH
        </p>
        <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 dark:text-gray-100 mb-6">
          DevSec Blueprint Curriculum
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto mb-4">
          A structured learning path for DevSecOps, Cloud Security engineering, and career growth.
        </p>
        <p className="text-base text-gray-600 dark:text-gray-400 max-w-3xl mx-auto mb-10">
          From secure pipelines and cloud architecture to career strategy and interview preparation.
          Build real skills, ship secure systems, and position yourself for the roles you actually want.
        </p>

        {/* Stats Row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 max-w-2xl mx-auto mb-10">
          <div className="text-center">
            <p className="text-2xl font-bold text-primary-500 dark:text-primary-400">3</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Stages</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-primary-500 dark:text-primary-400">18+</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Modules</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-primary-500 dark:text-primary-400">2</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Specialization Paths</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-primary-500 dark:text-primary-400">Real</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Capstone Projects</p>
          </div>
        </div>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link href="/pricing">
            <Button variant="primary" size="lg">
              Get Started
            </Button>
          </Link>
          <Link href="/about">
            <Button variant="secondary" size="lg">
              Learn About DSB
            </Button>
          </Link>
        </div>
      </div>
    </section>
  );
}
