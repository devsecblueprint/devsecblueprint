/**
 * Builder Journey Data File
 *
 * Typed data for the public-facing Builder Journey section on the homepage
 * and the authenticated Builder dashboard onboarding experience.
 *
 * The Builder Journey is a structured 60-day onboarding experience that guides
 * new Builder members through platform orientation, community connection,
 * foundational learning, technical specialization, and sustained engagement.
 *
 * The Free-tier journey follows the same structural pattern with tasks scoped
 * to resources that Free-tier members can access.
 */

export type JourneyTier = 'FREE' | 'BUILDER';

export interface BuilderJourneyTask {
  /** Unique slug identifier used as the progress-tracking key */
  id: string;
  /** Short task label */
  title: string;
  /** Brief description of what the task involves */
  description: string;
  /** Which membership tiers this task applies to */
  tiers: JourneyTier[];
}

export interface BuilderJourneyPhase {
  /** Phase number (1-5) */
  phase: number;
  /** Phase display title */
  title: string;
  /** Short objective statement */
  objective: string;
  /** Completion outcome summary */
  outcome: string;
  /** Icon identifier for rendering */
  icon: 'welcome' | 'community' | 'foundation' | 'path' | 'momentum';
  /** Tasks within this phase */
  tasks: BuilderJourneyTask[];
}

/**
 * Master journey phases with tier annotations on each task.
 * This is the single source of truth — all tier-specific exports derive from this.
 */
const JOURNEY_PHASES_ANNOTATED: BuilderJourneyPhase[] = [
  {
    phase: 1,
    title: 'Welcome to Builder',
    objective: 'Get oriented with the platform and connect your accounts.',
    outcome:
      'You understand how Builder works, where to find content, and how Discord integrates with the platform.',
    icon: 'welcome',
    tasks: [
      { id: 'connect-discord', title: 'Connect Discord account', description: 'Link your Discord to unlock Builder community channels.', tiers: ['FREE', 'BUILDER'] },
      { id: 'verify-builder-role', title: 'Verify Builder role assignment', description: 'Confirm your Builder role appears in Discord.', tiers: ['BUILDER'] },
      { id: 'complete-builder-profile', title: 'Complete Builder profile', description: 'Add your background and goals to your profile.', tiers: ['FREE', 'BUILDER'] },
      { id: 'review-community-guidelines', title: 'Review Community Guidelines', description: 'Understand how the community operates.', tiers: ['FREE', 'BUILDER'] },
      { id: 'explore-builder-dashboard', title: 'Explore the Builder dashboard', description: 'Tour the dashboard and key navigation areas.', tiers: ['FREE', 'BUILDER'] },
      { id: 'learn-platform-organization', title: 'Learn how the platform is organized', description: 'Understand learning paths, walkthroughs, and capstones.', tiers: ['FREE', 'BUILDER'] },
    ],
  },
  {
    phase: 2,
    title: 'Join the Community',
    objective: 'Connect with other Builders before starting technical learning.',
    outcome:
      'You feel connected to the Builder community and understand the recurring rhythm of Builder programming.',
    icon: 'community',
    tasks: [
      { id: 'introduce-yourself-discord', title: 'Introduce yourself in Discord', description: 'Post in the introductions channel.', tiers: ['FREE', 'BUILDER'] },
      { id: 'attend-first-office-hours', title: 'Attend your first Office Hours', description: 'Join a scheduled group session.', tiers: ['BUILDER'] },
      { id: 'participate-builder-session', title: 'Participate in a Builder Session', description: 'Attend a live technical session.', tiers: ['BUILDER'] },
      { id: 'join-technical-discussion', title: 'Join a technical discussion', description: 'Engage with other members on a topic.', tiers: ['FREE', 'BUILDER'] },
    ],
  },
  {
    phase: 3,
    title: 'Build Your Foundation',
    objective: 'Establish a common technical foundation before specializing.',
    outcome:
      'You have the foundational knowledge necessary to begin technical specialization with confidence.',
    icon: 'foundation',
    tasks: [
      { id: 'complete-prerequisites-path', title: 'Complete the Prerequisites learning path', description: 'Work through foundational content.', tiers: ['FREE', 'BUILDER'] },
      { id: 'complete-prerequisite-quizzes', title: 'Complete prerequisite quizzes', description: 'Validate your understanding.', tiers: ['FREE', 'BUILDER'] },
      { id: 'complete-introductory-activities', title: 'Complete introductory hands-on activities', description: 'Apply basics in guided exercises.', tiers: ['FREE', 'BUILDER'] },
      { id: 'review-engineering-specializations', title: 'Review available engineering specializations', description: 'Explore what comes next.', tiers: ['FREE', 'BUILDER'] },
    ],
  },
  {
    phase: 4,
    title: 'Choose Your Engineering Path',
    objective: 'Begin technical specialization through structured practice.',
    outcome:
      'You are applying knowledge through real-world engineering scenarios rather than isolated tutorials.',
    icon: 'path',
    tasks: [
      { id: 'select-primary-learning-path', title: 'Select a primary learning path', description: 'Choose your engineering focus area.', tiers: ['BUILDER'] },
      { id: 'begin-first-walkthrough', title: 'Begin the first walkthrough', description: 'Start building with guided instructions.', tiers: ['BUILDER'] },
      { id: 'complete-first-hands-on-project', title: 'Complete the first hands-on project', description: 'Deliver your first working project.', tiers: ['BUILDER'] },
      { id: 'complete-first-mini-capstone', title: 'Complete the first mini-capstone', description: 'Demonstrate applied understanding.', tiers: ['BUILDER'] },
      { id: 'begin-reading-content', title: 'Begin reading content', description: 'Start exploring available learning materials.', tiers: ['FREE'] },
      { id: 'review-learning-path-overview', title: 'Review learning path overview', description: 'Understand the structure of available learning paths.', tiers: ['FREE'] },
    ],
  },
  {
    phase: 5,
    title: 'Build Momentum',
    objective: 'Transition from onboarding into long-term participation.',
    outcome:
      'You complete onboarding and transition into the normal Builder experience with sustainable learning habits.',
    icon: 'momentum',
    tasks: [
      { id: 'complete-additional-walkthroughs', title: 'Complete additional walkthroughs', description: 'Continue deepening your skills.', tiers: ['BUILDER'] },
      { id: 'submit-first-capstone', title: 'Submit your first capstone', description: 'Deliver a substantial project for review.', tiers: ['BUILDER'] },
      { id: 'continue-learning-path', title: 'Continue your learning path', description: 'Make steady progress each week.', tiers: ['BUILDER'] },
      { id: 'participate-builder-events', title: 'Participate in Builder events', description: 'Stay engaged with live programming.', tiers: ['BUILDER'] },
      { id: 'establish-learning-goals', title: 'Establish learning goals', description: 'Set targets for the months ahead.', tiers: ['BUILDER'] },
      { id: 'continue-reading-content', title: 'Continue reading content', description: 'Keep making progress through available materials.', tiers: ['FREE'] },
      { id: 'participate-free-events', title: 'Participate in free community events', description: 'Stay engaged with community programming.', tiers: ['FREE'] },
      { id: 'set-learning-goals', title: 'Set learning goals', description: 'Set targets for the months ahead.', tiers: ['FREE'] },
      { id: 'explore-upgrade-options', title: 'Explore upgrade options', description: 'Learn about Builder-tier benefits and features.', tiers: ['FREE'] },
    ],
  },
];

// ---------------------------------------------------------------------------
// Tier filtering logic
// ---------------------------------------------------------------------------

/** Free-tier phase title overrides */
const FREE_PHASE_TITLES: Record<number, string> = {
  1: 'Welcome to DSB',
  2: 'Join the Community',
  3: 'Build Your Foundation',
  4: 'Start Learning',
  5: 'Next Steps',
};

/**
 * Filter the annotated phases to produce a tier-specific phase array.
 * Phases with no tasks for the target tier are omitted.
 */
function filterPhasesByTier(tier: JourneyTier): BuilderJourneyPhase[] {
  const titleOverrides = tier === 'FREE' ? FREE_PHASE_TITLES : {};

  return JOURNEY_PHASES_ANNOTATED
    .map((phase) => {
      const filteredTasks = phase.tasks.filter((task) => task.tiers.includes(tier));
      if (filteredTasks.length === 0) return null;
      return {
        ...phase,
        title: titleOverrides[phase.phase] || phase.title,
        tasks: filteredTasks,
      };
    })
    .filter((phase): phase is BuilderJourneyPhase => phase !== null);
}

// ---------------------------------------------------------------------------
// Tier-specific exports
// ---------------------------------------------------------------------------

/** Free-tier journey phases (filtered from shared data) */
export const FREE_JOURNEY_PHASES: BuilderJourneyPhase[] = filterPhasesByTier('FREE');

/** Builder-tier journey phases (filtered from shared data) */
export const BUILDER_JOURNEY_PHASES: BuilderJourneyPhase[] = filterPhasesByTier('BUILDER');

/** Total number of Free-tier tasks */
export const FREE_JOURNEY_TOTAL_TASKS: number = FREE_JOURNEY_PHASES.reduce(
  (sum, phase) => sum + phase.tasks.length,
  0,
);

/** Total number of Builder-tier tasks */
export const BUILDER_JOURNEY_TOTAL_TASKS: number = BUILDER_JOURNEY_PHASES.reduce(
  (sum, phase) => sum + phase.tasks.length,
  0,
);

/** Flat array of all Free-tier task IDs */
export const FREE_JOURNEY_ALL_TASK_IDS: string[] = FREE_JOURNEY_PHASES.flatMap(
  (phase) => phase.tasks.map((task) => task.id),
);

/** Flat array of all Builder-tier task IDs */
export const BUILDER_JOURNEY_ALL_TASK_IDS: string[] = BUILDER_JOURNEY_PHASES.flatMap(
  (phase) => phase.tasks.map((task) => task.id),
);

/** Section copy for the public homepage */
export const BUILDER_JOURNEY_SECTION = {
  title: 'Your Builder Journey',
  subtitle:
    'Every Builder member follows a structured onboarding experience designed to help you build confidence, establish strong engineering fundamentals, and become an active member of The DevSec Blueprint community.',
  note: 'Most members complete this journey during their first 60 days, although everyone is encouraged to progress at their own pace.',
  cta: {
    label: 'Become a Builder',
    href: '/pricing',
  },
} as const;
