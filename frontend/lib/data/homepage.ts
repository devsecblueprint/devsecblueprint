/**
 * Homepage content data.
 * Separates content from presentation for maintainability.
 */

import {
  METRIC_ACTIVE_USERS,
  METRIC_CONTENT_VIEWS,
  METRIC_PLATFORM_EVENTS,
  METRIC_LINKEDIN_FOLLOWERS,
  METRICS_DISCLOSURE,
} from './metrics';

export interface HomepageMetric {
  value: string;
  label: string;
  icon: 'users' | 'views' | 'events' | 'linkedin';
}

export interface HomepageBenefit {
  title: string;
  description: string;
  icon: 'curriculum' | 'walkthroughs' | 'projects' | 'reviews' | 'community' | 'career' | 'recordings';
}

export const HOMEPAGE_METRICS: HomepageMetric[] = [
  {
    value: METRIC_ACTIVE_USERS.value,
    label: METRIC_ACTIVE_USERS.label,
    icon: 'users',
  },
  {
    value: METRIC_CONTENT_VIEWS.value,
    label: METRIC_CONTENT_VIEWS.label,
    icon: 'views',
  },
  {
    value: METRIC_PLATFORM_EVENTS.value,
    label: METRIC_PLATFORM_EVENTS.label,
    icon: 'events',
  },
  {
    value: METRIC_LINKEDIN_FOLLOWERS.value,
    label: METRIC_LINKEDIN_FOLLOWERS.label,
    icon: 'linkedin',
  },
];

export const HOMEPAGE_METRICS_DISCLOSURE = METRICS_DISCLOSURE;

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
  {
    title: 'Recorded Builder Sessions',
    description:
      'Miss a live session or want to revisit what you learned? Builders can watch recorded sessions on demand and return to technical walkthroughs, discussions, and hands-on learning anytime.',
    icon: 'recordings',
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
