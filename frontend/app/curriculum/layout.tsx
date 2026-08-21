import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Curriculum | The DevSec Blueprint',
  description:
    'Explore the structured DevSecOps and Cloud Security curriculum. From secure pipelines and cloud architecture to career strategy.',
  alternates: { canonical: '/curriculum' },
  openGraph: {
    title: 'Curriculum | The DevSec Blueprint',
    description:
      'Explore the structured DevSecOps and Cloud Security curriculum. From secure pipelines and cloud architecture to career strategy.',
    url: '/curriculum',
  },
};

export default function CurriculumLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
