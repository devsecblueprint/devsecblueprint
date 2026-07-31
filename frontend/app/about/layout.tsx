import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: {
    template: '%s | The DevSec Blueprint',
    default: 'About The DevSec Blueprint',
  },
};

export default function AboutLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
