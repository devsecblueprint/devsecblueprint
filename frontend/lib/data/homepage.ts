/**
 * Homepage content data.
 * Separates content from presentation for maintainability.
 */

export interface HomepageMetric {
  value: string;
  label: string;
  icon: 'globe' | 'users' | 'interactions' | 'linkedin';
}

export interface HomepageBenefit {
  title: string;
  description: string;
  icon: 'curriculum' | 'walkthroughs' | 'projects' | 'reviews' | 'community' | 'career';
}

export const HOMEPAGE_METRICS: HomepageMetric[] = [
  {
    value: '143',
    label: 'Countries Represented',
    icon: 'globe',
  },
  {
    value: '800+',
    label: 'Registered Platform Users',
    icon: 'users',
  },
  {
    value: '10,000+',
    label: 'Platform Interactions',
    icon: 'interactions',
  },
  {
    value: '1,000+',
    label: 'LinkedIn Followers',
    icon: 'linkedin',
  },
];

export const HOMEPAGE_METRICS_DISCLOSURE =
  'All growth is organic — no paid advertising. Geographic reach and platform interactions are based on Google Analytics data from January to July 2026. Community totals are current as of July 2026.';

export const HOMEPAGE_BENEFITS: HomepageBenefit[] = [
  {
    title: 'Structured Curriculum',
    description:
      'Build foundational understanding through carefully organized DevSecOps and cloud security content.',
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
