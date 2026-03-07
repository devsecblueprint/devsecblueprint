import { LearningPath, Module, UserStats, Badge } from './types';

export const LEARNING_PATHS: LearningPath[] = [
  {
    id: '1',
    title: 'Prerequisites',
    description: 'Essential foundational knowledge and skills you need before diving into DevSecOps and cloud security. Cover the basics of programming, networking, and security concepts.',
    slug: 'prerequisites',
    moduleCount: 5
  },
  {
    id: '2',
    title: 'Soft Skills',
    description: 'Communication, collaboration, and leadership skills that make you effective in security roles. Learn how to advocate for security, work with cross-functional teams, and drive cultural change.',
    slug: 'soft-skills',
    moduleCount: 4
  },
  {
    id: '3',
    title: 'DevSecOps',
    description: 'I bring security into every step of the pipeline. From Jenkins to GitHub Actions, I\'ve embedded tools like Trivy and SonarQube to catch issues before they become problems. I am an advocate for building secure, automated workflows that scale across teams and environments.',
    slug: 'devsecops',
    moduleCount: 8
  },
  {
    id: '4',
    title: 'Cloud Security Development',
    description: 'I design and secure cloud infrastructure in AWS and GCP with a focus on doing things the right way. IAM hardening, compliance guardrails, and detection controls included. Whether it\'s Terraform or Docker, I\'m all about shipping secure by default.',
    slug: 'cloud-security',
    moduleCount: 9
  },
  {
    id: '5',
    title: 'Sample Projects',
    description: 'Hands-on projects that bring together everything you\'ve learned. Build real-world applications with security baked in from the start, from CI/CD pipelines to cloud infrastructure.',
    slug: 'sample-projects',
    moduleCount: 6
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
