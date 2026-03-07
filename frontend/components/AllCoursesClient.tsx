'use client';

import { useEffect, useState } from 'react';
import { getAllCourses, getLearningPathTitle, CourseProgress } from '@/lib/course-utils';
import { useAllProgress } from '@/lib/hooks/useAllProgress';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { Badge } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Spinner';

export function AllCoursesClient() {
  const { progress, isLoading } = useAllProgress();
  const [courses, setCourses] = useState<CourseProgress[]>([]);
  const [groupedCourses, setGroupedCourses] = useState<{ [key: string]: CourseProgress[] }>({});

  useEffect(() => {
    // Recalculate courses whenever progress changes, filtering out walkthroughs
    const allCourses = getAllCourses(progress).filter(course => 
      course.learningPath !== 'Walkthroughs'
    );
    setCourses(allCourses);

    // Group courses by learning path
    const grouped = allCourses.reduce((acc, course) => {
      if (!acc[course.learningPath]) {
        acc[course.learningPath] = [];
      }
      acc[course.learningPath].push(course);
      return acc;
    }, {} as { [key: string]: CourseProgress[] });

    setGroupedCourses(grouped);
  }, [progress]);

  // Show loading spinner while fetching progress
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (courses.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600 dark:text-gray-400">No courses available yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-12">
      {/* Sort learning paths with "welcome" first, then "Getting Started", then "Know Before You Go" */}
      {Object.entries(groupedCourses)
        .sort(([pathA], [pathB]) => {
          // Normalize path names to lowercase for comparison
          const normalizedA = pathA.toLowerCase();
          const normalizedB = pathB.toLowerCase();
          
          if (normalizedA === 'welcome') return -1;
          if (normalizedB === 'welcome') return 1;
          if (normalizedA === 'getting started') return -1;
          if (normalizedB === 'getting started') return 1;
          if (normalizedA === 'know before you go') return -1;
          if (normalizedB === 'know before you go') return 1;
          return pathA.localeCompare(pathB);
        })
        .map(([learningPath, pathCourses]) => (
        <div key={learningPath}>
          {/* Learning Path Header */}
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              {getLearningPathTitle(learningPath)}
            </h2>
            <div className="h-1 w-20 bg-primary-400 rounded"></div>
          </div>

          {/* Courses Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {pathCourses.map((course) => (
              <a
                key={`${course.learningPath}/${course.topic}`}
                href={course.firstPageSlug}
                className="block group"
              >
                <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-6 hover:border-primary-400 dark:hover:border-primary-400 transition-all hover:shadow-lg">
                  {/* Course Header */}
                  <div className="flex items-start justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 group-hover:text-primary-500 dark:group-hover:text-primary-400 transition-colors">
                      {course.title}
                    </h3>
                    {course.percentComplete === 100 && (
                      <Badge variant="success" size="sm">
                        Complete
                      </Badge>
                    )}
                  </div>

                  {/* Progress Info */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">
                        {course.completedPages} of {course.totalPages} lessons
                      </span>
                      <span className="font-semibold text-gray-900 dark:text-gray-100">
                        {course.percentComplete}%
                      </span>
                    </div>

                    {/* Progress Bar */}
                    <ProgressBar 
                      percentage={course.percentComplete} 
                      height="sm"
                    />
                  </div>

                  {/* Action Button */}
                  <div className="mt-6">
                    <div className="flex items-center text-primary-500 dark:text-primary-400 font-medium text-sm group-hover:text-primary-600 dark:group-hover:text-primary-300 transition-colors">
                      {course.percentComplete === 0 ? (
                        <>
                          <span>Start Course</span>
                          <svg className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </>
                      ) : course.percentComplete === 100 ? (
                        <>
                          <span>Review Course</span>
                          <svg className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </>
                      ) : (
                        <>
                          <span>Continue Learning</span>
                          <svg className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </a>
            ))}
          </div>
        </div>
      ))}

      {/* Overall Stats */}
      <div className="mt-12 pt-8 border-t border-gray-200 dark:border-gray-800">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-6">
            <div className="text-3xl font-bold text-primary-500 dark:text-primary-400 mb-2">
              {courses.length}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Total Courses
            </div>
          </div>

          <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-6">
            <div className="text-3xl font-bold text-primary-500 dark:text-primary-400 mb-2">
              {courses.filter(c => c.percentComplete === 100).length}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Completed Courses
            </div>
          </div>

          <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-6">
            <div className="text-3xl font-bold text-primary-500 dark:text-primary-400 mb-2">
              {courses.reduce((sum, c) => sum + c.completedPages, 0)}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Total Lessons Completed
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
