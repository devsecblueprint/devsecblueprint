import { CURRICULUM_STAGES } from '@/lib/curriculum-data';
import { StageSection } from './StageSection';

export function CurriculumStages() {
  // Group stages by stage number to handle parallel paths
  const stage1 = CURRICULUM_STAGES.find(s => s.stageNumber === 1);
  const stage2Options = CURRICULUM_STAGES.filter(s => s.stageNumber === 2);
  const stage3 = CURRICULUM_STAGES.find(s => s.stageNumber === 3);

  return (
    <div className="px-4 sm:px-6 py-8 sm:py-12">
      <div className="max-w-7xl mx-auto">
        {/* Timeline Container */}
        <div className="space-y-12">
          {/* Stage 1 */}
          {stage1 && (
            <div className="max-w-5xl mx-auto">
              <StageSection stage={stage1} isLast={false} />
            </div>
          )}

          {/* Stage 2 - Parallel Paths */}
          {stage2Options.length > 0 && (
            <div className="relative">
              {/* Branching indicator */}
              <div className="flex justify-center mb-8">
                <div className="text-center px-6 py-3 bg-primary-50 dark:bg-primary-900/20 rounded-full border-2 border-primary-400 dark:border-primary-500">
                  <p className="text-sm font-semibold text-primary-700 dark:text-primary-300">
                    Choose Your Path
                  </p>
                </div>
              </div>

              {/* Side by side paths */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">
                {stage2Options.map((stage) => (
                  <div key={stage.id}>
                    <StageSection stage={stage} isLast={false} />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Stage 3 */}
          {stage3 && (
            <div className="max-w-5xl mx-auto">
              <StageSection stage={stage3} isLast={true} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
