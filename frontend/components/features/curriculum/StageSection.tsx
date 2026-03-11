'use client';

import { useState } from 'react';
import { ModuleCard } from './ModuleCard';
import { CurriculumStage } from '@/lib/types';

export interface StageSectionProps {
  stage: CurriculumStage;
  isLast?: boolean;
}

export function StageSection({ stage, isLast = false }: StageSectionProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="relative">
      {/* Timeline connector line */}
      {!isLast && (
        <div className="absolute left-6 top-20 bottom-0 w-0.5 bg-gradient-to-b from-primary-400 via-primary-300 to-primary-200 dark:from-primary-500 dark:via-primary-600 dark:to-primary-700" />
      )}

      <div className="relative">
        {/* Stage Header - Interactive */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full text-left group"
          aria-expanded={isExpanded}
        >
          <div className="flex items-start space-x-6">
            {/* Timeline Node */}
            <div className="relative flex-shrink-0 z-10">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary-400 to-primary-500 dark:from-primary-500 dark:to-primary-600 text-gray-900 dark:text-white flex items-center justify-center font-bold text-lg shadow-lg ring-4 ring-white dark:ring-gray-950 transition-transform group-hover:scale-110">
                {stage.stageNumber || 1}
              </div>
              {/* Pulse effect when collapsed */}
              {!isExpanded && (
                <div className="absolute inset-0 rounded-full bg-primary-400 dark:bg-primary-500 animate-ping opacity-20" />
              )}
            </div>

            {/* Stage Info Card */}
            <div className="flex-1 bg-white dark:bg-gray-900 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-800 p-6 transition-all group-hover:shadow-xl group-hover:border-primary-400 dark:group-hover:border-primary-500">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                    {stage.name}
                  </h2>
                  <p className="text-gray-600 dark:text-gray-400 mb-3">
                    {stage.description}
                  </p>
                  {stage.moduleCount && (
                    <div className="flex items-center space-x-2 text-sm text-primary-600 dark:text-primary-400">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                      </svg>
                      <span className="font-semibold">{stage.moduleCount} modules</span>
                    </div>
                  )}
                </div>

                {/* Expand/Collapse Icon */}
                <div className="ml-4">
                  <svg
                    className={`w-6 h-6 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </button>

        {/* Expandable Content */}
        <div
          className={`overflow-hidden transition-all duration-500 ease-in-out ${
            isExpanded ? 'max-h-[10000px] opacity-100' : 'max-h-0 opacity-0'
          }`}
        >
          <div className="ml-[4.5rem] mt-6 space-y-6">
            {/* Modules - Single Column */}
            {stage.modules && stage.modules.length > 0 && (
              <div className="space-y-4">
                {stage.modules.map((module, index) => (
                  <div
                    key={module.id}
                    className="animate-fadeIn"
                    style={{ animationDelay: `${index * 50}ms` }}
                  >
                    <ModuleCard module={module} />
                  </div>
                ))}
              </div>
            )}

            {/* Capstone Projects */}
            {stage.projects && stage.projects.length > 0 && (
              <div className="bg-gradient-to-br from-primary-50 to-amber-50 dark:from-gray-900 dark:to-gray-800 rounded-2xl p-6 border border-primary-200 dark:border-primary-900">
                <div className="flex items-center space-x-2 mb-4">
                  <svg className="w-6 h-6 text-primary-600 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                  </svg>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    Capstone Projects
                  </h3>
                </div>
                <ul className="space-y-3">
                  {stage.projects.map((project, index) => (
                    <li key={index} className="flex items-start space-x-3">
                      <span className="flex-shrink-0 w-6 h-6 rounded-full bg-primary-400 text-white flex items-center justify-center text-sm font-semibold">
                        {index + 1}
                      </span>
                      <span className="text-gray-700 dark:text-gray-300 font-medium">{project}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
