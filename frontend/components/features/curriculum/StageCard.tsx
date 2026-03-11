import { Card } from '@/components/ui/Card';
import { CurriculumStage } from '@/lib/types';

export interface StageCardProps {
  stage: CurriculumStage;
}

export function StageCard({ stage }: StageCardProps) {
  return (
    <Card className="bg-gradient-to-br from-primary-50 to-white dark:from-gray-900 dark:to-gray-900/50">
      <div className="space-y-3">
        <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
          {stage.description}
        </p>
        {stage.moduleCount && (
          <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <span>{stage.moduleCount} modules</span>
          </div>
        )}
      </div>
    </Card>
  );
}
