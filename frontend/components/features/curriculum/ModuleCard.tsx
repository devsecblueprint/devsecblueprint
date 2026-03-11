'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { CurriculumModule } from '@/lib/types';

export interface ModuleCardProps {
  module: CurriculumModule;
}

export function ModuleCard({ module }: ModuleCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <Card className="transition-all duration-300 hover:shadow-xl border-l-4 border-l-primary-400 dark:border-l-primary-500 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full text-left"
      >
        <div className="space-y-4">
          {/* Title and Description */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
              {module.name}
            </h3>
            {module.description && (
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {module.description}
              </p>
            )}
          </div>
          
          {/* Topics - Always visible */}
          <ul className="space-y-2.5">
            {module.topics.map((topic, index) => (
              <li 
                key={index} 
                className="flex items-start space-x-3 text-sm text-gray-600 dark:text-gray-400 group"
              >
                <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-primary-400 mt-2 group-hover:scale-150 transition-transform" />
                <span className="group-hover:text-gray-900 dark:group-hover:text-gray-200 transition-colors">
                  {topic}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </button>

      {/* Expandable Submodules Timeline */}
      {module.submodules && module.submodules.length > 0 && (
        <div
          className={`overflow-hidden transition-all duration-500 ease-in-out ${
            isExpanded ? 'max-h-[2000px] opacity-100 mt-6' : 'max-h-0 opacity-0'
          }`}
        >
          <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
            <div className="flex items-center space-x-2 mb-4">
              <svg className="w-5 h-5 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                Lessons ({module.submodules.length})
              </h4>
            </div>

            {/* Nested Timeline */}
            <div className="relative space-y-3 pl-4">
              {/* Timeline line */}
              <div className="absolute left-2 top-2 bottom-2 w-px bg-gradient-to-b from-primary-300 via-primary-200 to-transparent dark:from-primary-600 dark:via-primary-700 dark:to-transparent" />

              {module.submodules.map((submodule, index) => (
                <div
                  key={submodule.id}
                  className="relative flex items-start space-x-3 group animate-fadeIn"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  {/* Timeline node */}
                  <div className="relative z-10 flex-shrink-0">
                    <div className="w-4 h-4 rounded-full bg-white dark:bg-gray-900 border-2 border-primary-400 dark:border-primary-500 group-hover:scale-125 transition-transform" />
                  </div>

                  {/* Submodule info */}
                  <div className="flex-1 bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3 group-hover:bg-gray-100 dark:group-hover:bg-gray-800 transition-colors">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <span className="text-xs font-semibold text-primary-600 dark:text-primary-400">
                            Lesson {submodule.moduleNumber}
                          </span>
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            •
                          </span>
                          <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center space-x-1">
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span>{submodule.readingTime} min</span>
                          </span>
                        </div>
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {submodule.title}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}
