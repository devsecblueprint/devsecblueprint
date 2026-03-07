'use client';

import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { AllCoursesClient } from '@/components/AllCoursesClient';

export default function LearnPage() {
  return (
    <>
      <NavbarWithAuth />
      
      <main className="min-h-screen pt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          {/* Header */}
          <div className="mb-12">
            <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4">
              All Courses
            </h1>
            <p className="text-lg text-gray-600 dark:text-gray-400">
              Track your progress across all learning paths
            </p>
          </div>

          {/* Courses Grid */}
          <AllCoursesClient />
        </div>
      </main>
    </>
  );
}
