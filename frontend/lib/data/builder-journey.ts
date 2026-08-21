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
  /** URL the user should visit to accomplish this task. External links open in a new tab. */
  actionUrl: string;
  /** Whether this task is auto-completed by the system (no manual action needed beyond visiting) */
  autoDetect?: boolean;
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
      { id: 'connect-discord', title: 'Connect Discord account', description: 'Go to Settings > Connections and link your Discord account to access community channels and get real-time updates.', tiers: ['FREE', 'BUILDER'], actionUrl: '/dashboard/settings', autoDetect: true },
      { id: 'schedule-onboarding-call', title: 'Schedule your onboarding call', description: 'Book a one-on-one onboarding session with Iman to discuss your goals, ask questions about the program, and get personalized guidance on where to start.', tiers: ['BUILDER'], actionUrl: 'https://calendar.app.google/Dt32AXvvfpmGKxB86' },
      { id: 'verify-builder-role', title: 'Verify Builder role assignment', description: 'Open Discord and confirm the "Builder" role badge appears next to your username in the DSB server.', tiers: ['BUILDER'], actionUrl: 'https://discord.gg/3HdZ9K6Sdw' },
      { id: 'review-community-guidelines', title: 'Review Community Guidelines', description: 'Read the Community Guidelines page to understand how members collaborate, ask questions, and share work in the welcome message channel in the Discord.', tiers: ['FREE', 'BUILDER'], actionUrl: 'https://discord.gg/3HdZ9K6Sdw' },
      { id: 'explore-builder-dashboard', title: 'Explore the Builder dashboard', description: 'Visit each section of your dashboard — progress tracking, learning paths, notifications, and community feed.', tiers: ['FREE', 'BUILDER'], actionUrl: '/dashboard', autoDetect: true },
      { id: 'learn-platform-organization', title: 'Learn how the platform is organized', description: 'Understand the structure: learning paths contain walkthroughs (guided builds) and capstones (independent projects).', tiers: ['FREE', 'BUILDER'], actionUrl: '/learn', autoDetect: true },
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
      { id: 'introduce-yourself-discord', title: 'Introduce yourself in Discord', description: 'Post a short intro in #introductions — share your background, what you want to learn, and what brought you here.', tiers: ['FREE', 'BUILDER'], actionUrl: 'https://discord.gg/3HdZ9K6Sdw' },
      { id: 'attend-first-office-hours', title: 'Attend your first Office Hours', description: 'Join a live weekly Office Hours session where members ask questions and get real-time help from the community.', tiers: ['BUILDER'], actionUrl: 'https://discord.gg/3HdZ9K6Sdw' },
      { id: 'participate-builder-session', title: 'Participate in a Builder Session', description: 'Attend a scheduled Builder Session — a live, hands-on technical workshop led by a community member or mentor.', tiers: ['BUILDER'], actionUrl: 'https://discord.gg/3HdZ9K6Sdw' },
      { id: 'join-technical-discussion', title: 'Join a technical discussion', description: 'Reply to or start a thread in a technical channel — share your perspective on a tool, concept, or approach.', tiers: ['FREE', 'BUILDER'], actionUrl: 'https://discord.gg/3HdZ9K6Sdw' },
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
      { id: 'complete-prerequisites-path', title: 'Complete the Prerequisites learning path', description: 'Work through Linux, networking, cloud computing, version control, and scripting fundamentals in the Prerequisites path.', tiers: ['FREE', 'BUILDER'], actionUrl: '/learn/know_before_you_go/prerequisites/module_1', autoDetect: true },
      { id: 'complete-prerequisite-quizzes', title: 'Complete prerequisite quizzes', description: 'Pass the quiz at the end of each prerequisite module to confirm your understanding before moving on.', tiers: ['FREE', 'BUILDER'], actionUrl: '/learn/prerequisites', autoDetect: true },
      { id: 'complete-introductory-activities', title: 'Complete introductory hands-on activities', description: 'Follow the guided exercises in the Prerequisites path to practice commands, configs, and basic tooling hands-on.', tiers: ['FREE', 'BUILDER'], actionUrl: '/learn/prerequisites', autoDetect: true },
      { id: 'review-engineering-specializations', title: 'Review available engineering specializations', description: 'Browse the DevSecOps, Cloud Security, and Application Security learning paths to see which aligns with your goals.', tiers: ['FREE', 'BUILDER'], actionUrl: '/learn', autoDetect: true },
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
      { id: 'select-primary-learning-path', title: 'Select a primary learning path', description: 'Choose DevSecOps, Cloud Security, or Application Security as your primary specialization track.', tiers: ['BUILDER'], actionUrl: '/learn' },
      { id: 'begin-first-walkthrough', title: 'Begin the first walkthrough', description: 'Start your first guided walkthrough — follow step-by-step instructions to build a real security project from scratch.', tiers: ['BUILDER'], actionUrl: '/learn', autoDetect: true },
      { id: 'complete-first-hands-on-project', title: 'Complete the first hands-on project', description: 'Finish building your first walkthrough project end-to-end and verify it works as expected.', tiers: ['BUILDER'], actionUrl: '/learn', autoDetect: true },
      { id: 'begin-reading-content', title: 'Begin reading content', description: 'Start reading through the learning material in your chosen specialization — concepts, architecture, and best practices.', tiers: ['FREE'], actionUrl: '/learn', autoDetect: true },
      { id: 'review-learning-path-overview', title: 'Review learning path overview', description: 'Read the overview page of a learning path to understand its modules, progression, and what you will be able to build.', tiers: ['FREE'], actionUrl: '/learn' },
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
      { id: 'complete-additional-walkthroughs', title: 'Complete additional walkthroughs', description: 'Work through more guided walkthroughs in your learning path to deepen your skills across different scenarios.', tiers: ['BUILDER'], actionUrl: '/learn', autoDetect: true },
      { id: 'submit-first-capstone', title: 'Submit your first capstone', description: 'Build and submit a full capstone project — an independent, portfolio-ready deliverable reviewed by the community.', tiers: ['BUILDER'], actionUrl: '/learn', autoDetect: true },
      { id: 'continue-learning-path', title: 'Continue your learning path', description: 'Keep progressing through your specialization track — aim for at least one module or walkthrough per week.', tiers: ['BUILDER'], actionUrl: '/learn' },
      { id: 'participate-builder-events', title: 'Participate in Builder events', description: 'Join recurring Builder events like study groups, pair programming sessions, or community demo days.', tiers: ['BUILDER'], actionUrl: 'https://discord.gg/3HdZ9K6Sdw' },
      { id: 'establish-learning-goals', title: 'Establish learning goals', description: 'Set specific targets for the next 30-60 days — which modules to finish, which capstone to tackle, or skills to develop.', tiers: ['BUILDER'], actionUrl: '/dashboard' },
      { id: 'continue-reading-content', title: 'Continue reading content', description: 'Keep reading through your learning path modules — aim to finish at least one new section each week.', tiers: ['FREE'], actionUrl: '/learn' },
      { id: 'participate-free-events', title: 'Participate in free community events', description: 'Join open community events like Q&A sessions, study groups, or public demos happening in Discord.', tiers: ['FREE'], actionUrl: 'https://discord.gg/3HdZ9K6Sdw' },
      { id: 'set-learning-goals', title: 'Set learning goals', description: 'Define what you want to achieve in the next 30 days — topics to cover, skills to practice, or paths to explore.', tiers: ['FREE'], actionUrl: '/dashboard' },
      { id: 'explore-upgrade-options', title: 'Explore upgrade options', description: 'Visit the pricing page to see how Builder-tier access unlocks walkthroughs, capstones, and live sessions.', tiers: ['FREE'], actionUrl: '/pricing' },
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
  title: 'What Your First 60 Days Looks Like',
  subtitle:
    'Every Builder receives a structured onboarding guide designed to help you build confidence, establish strong engineering fundamentals, and become an active member of The DevSec Blueprint community.',
  note: 'Most Builders complete this guide during their first 60 days, although everyone is encouraged to progress at their own pace.',
  cta: {
    label: 'Become a Builder',
    href: '/pricing',
  },
} as const;
