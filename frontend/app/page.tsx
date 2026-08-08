import type { Metadata } from 'next';
import { HomePageClient } from '@/components/features/HomePageClient';

export const metadata: Metadata = {
  title: 'The DevSec Blueprint | Practical DevSecOps & Cloud Security Training',
  description:
    'Advance your career in DevSecOps and Cloud Security through structured learning paths, hands-on projects, guided walkthroughs, and a community of engineers building real-world skills together.',
  keywords: [
    'DevSecOps training',
    'Cloud Security course',
    'hands-on security engineering',
    'AWS security',
    'CI/CD security',
    'application security',
    'DevOps security',
    'community security training',
  ],
  alternates: { canonical: '/' },
  openGraph: {
    title: 'The DevSec Blueprint | Practical DevSecOps & Cloud Security Training',
    description:
      'Advance your career in DevSecOps and Cloud Security through structured learning paths, hands-on projects, guided walkthroughs, and a community of engineers building real-world skills together.',
    url: '/',
    type: 'website',
  },
};

export default function Home() {
  return <HomePageClient />;
}
