import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Pricing | The DevSec Blueprint',
  description:
    'Join DSB Builder for structured DevSecOps and Cloud Security curriculum, real engineering projects, technical feedback, and community support.',
  alternates: { canonical: '/pricing' },
  openGraph: {
    title: 'Pricing | The DevSec Blueprint',
    description:
      'Join DSB Builder for structured DevSecOps and Cloud Security curriculum, real engineering projects, technical feedback, and community support.',
    url: '/pricing',
  },
};

export default function PricingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
