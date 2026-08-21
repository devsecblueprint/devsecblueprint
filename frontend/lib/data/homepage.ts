/**
 * Homepage content data.
 * Separates content from presentation for maintainability.
 */

export interface HomepageMetric {
  value: string;
  label: string;
  icon: 'users' | 'views' | 'events' | 'linkedin';
}

export interface HomepageBenefit {
  title: string;
  description: string;
  icon: 'curriculum' | 'walkthroughs' | 'projects' | 'reviews' | 'community' | 'career';
}

export const HOMEPAGE_METRICS: HomepageMetric[] = [
  {
    value: '13K+',
    label: 'Active Users',
    icon: 'users',
  },
  {
    value: '51K+',
    label: 'Content Views',
    icon: 'views',
  },
  {
    value: '124K+',
    label: 'Platform Events',
    icon: 'events',
  },
  {
    value: '1,000+',
    label: 'LinkedIn Followers',
    icon: 'linkedin',
  },
];

export const HOMEPAGE_METRICS_DISCLOSURE =
  'Platform metrics reflect January–August 2026 data sourced from Google Analytics. Active Users reflects unique visitors who engaged with the platform. All growth is organic — no paid advertising.';

export const HOMEPAGE_BENEFITS: HomepageBenefit[] = [
  {
    title: 'Structured Curriculum',
    description:
      'Build foundational understanding through carefully organized DevSecOps and Cloud Security content.',
    icon: 'curriculum',
  },
  {
    title: 'Expert-Written Walkthroughs',
    description:
      'Follow detailed technical implementations that explain both what to build and why the decisions matter.',
    icon: 'walkthroughs',
  },
  {
    title: 'Guided Projects and Mini-Capstones',
    description:
      'Apply concepts by building practical solutions to real security engineering problems.',
    icon: 'projects',
  },
  {
    title: 'Project Reviews and Feedback',
    description:
      'Submit eligible work for technical review and receive feedback designed to help you improve.',
    icon: 'reviews',
  },
  {
    title: 'Community and Office Hours',
    description:
      'Learn alongside other builders, discuss technical challenges, and participate in scheduled group sessions.',
    icon: 'community',
  },
  {
    title: 'Career Development Resources',
    description:
      'Strengthen your resume, LinkedIn presence, portfolio, interview strategy, and ability to communicate technical experience.',
    icon: 'career',
  },
];

export const REGISTRATION_CALLOUT_FEATURES = [
  'Access available expert-written walkthroughs',
  'Explore structured learning tracks and guided capstones',
  'Submit eligible projects for technical review',
  'Join private Builder discussions and community programming',
  'Participate in scheduled group office hours',
  'Access premium templates, references, and career resources based on membership',
];
