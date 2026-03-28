import { LearningPath, Module, UserStats, Badge } from './types';

export const LEARNING_PATHS: LearningPath[] = [
  {
    id: '1',
    title: 'Prerequisites',
    description: 'Build the foundation you need before diving into DevSecOps and cloud security development. This section covers core concepts like programming, networking, Linux, cloud fundamentals, and security basics that will help everything else make more sense.',
    slug: 'prerequisites',
    moduleCount: 5
  },
  {
    id: '2',
    title: 'Soft Skills',
    description: 'Technical skills matter, but so does how you work with people. Learn how to communicate security clearly, collaborate across teams, influence decisions, and build the kind of mindset needed to be effective in real engineering environments.',
    slug: 'soft-skills',
    moduleCount: 4
  },
  {
    id: '3',
    title: 'DevSecOps',
    description: 'Learn how to integrate security into the software delivery lifecycle without slowing engineering to a halt. This path focuses on secure CI/CD, pipeline security, automation, shift-left practices, application security tooling, and building workflows that help teams ship safer code with confidence.',
    slug: 'devsecops',
    moduleCount: 8
  },
  {
    id: '4',
    title: 'Cloud Security Development',
    description: 'Learn how to design, build, and secure cloud environments with security built in from the start. This path focuses on IAM, infrastructure as code, cloud architecture, preventive controls, detective controls, compliance-minded design, and secure deployment patterns across modern cloud platforms.',
    slug: 'cloud-security',
    moduleCount: 9
  },
  {
    id: '5',
    title: 'Walkthroughs',
    description: 'Apply what you\'ve learned through hands-on projects designed to connect concepts with implementation. These projects help you practice building secure pipelines, cloud infrastructure, and real-world systems where security is treated as part of the engineering process, not an afterthought.',
    slug: 'walkthroughs',
    moduleCount: 6
  },
  {
    id: '6',
    title: 'Capstones',
    description: 'Capstones are where you bring everything together. These larger, end-to-end projects are designed to test how well you can apply what you\'ve learned across multiple areas, from secure pipelines to cloud architecture and security controls. The goal is to move beyond isolated exercises and demonstrate real-world problem solving through practical implementation.',
    slug: 'capstones',
    moduleCount: 0
  }
];

export const SAMPLE_MODULES: Module[] = [
  {
    id: 'm1',
    title: 'Introduction to DevSecOps',
    order: 1,
    pages: [
      { id: 'p1', title: 'What is DevSecOps?', slug: 'what-is-devsecops', order: 1, completed: true },
      { id: 'p2', title: 'Core Principles', slug: 'core-principles', order: 2, completed: true },
      { id: 'p3', title: 'Security Culture', slug: 'security-culture', order: 3, completed: false }
    ]
  },
  {
    id: 'm2',
    title: 'Threat Modeling',
    order: 2,
    pages: [
      { id: 'p4', title: 'Introduction to Threat Modeling', slug: 'intro-threat-modeling', order: 1, completed: false },
      { id: 'p5', title: 'STRIDE Framework', slug: 'stride', order: 2, completed: false }
    ]
  }
];

export const SAMPLE_USER_STATS: UserStats = {
  currentStreak: 0,
  longestStreak: 0,
  overallCompletion: 0,
  badgesEarned: 0
};

export const SAMPLE_BADGES: Badge[] = [
  {
    id: 'b1',
    title: 'First Steps',
    description: 'Complete your first lesson',
    icon: '🎯',
    earned: true,
    earnedDate: '2024-01-15'
  },
  {
    id: 'b2',
    title: 'Week Warrior',
    description: 'Maintain a 7-day streak',
    icon: '🔥',
    earned: true,
    earnedDate: '2024-01-22'
  },
  {
    id: 'b3',
    title: 'Security Champion',
    description: 'Complete the Secure SDLC path',
    icon: '🛡️',
    earned: false
  },
  {
    id: 'b4',
    title: 'Code Guardian',
    description: 'Complete the Application Security path',
    icon: '🔒',
    earned: false
  },
  {
    id: 'b5',
    title: 'Infrastructure Expert',
    description: 'Complete the IaC path',
    icon: '⚙️',
    earned: false
  }
];
