import type { Metadata } from 'next';
import Link from 'next/link';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { Footer } from '@/components/layout/Footer';
import { FAQ_CATEGORIES } from '@/lib/data/faq';
import FAQClient from './FAQClient';

export const metadata: Metadata = {
  title: 'Frequently Asked Questions | The DevSec Blueprint',
  description: 'Find answers to common questions about The DevSec Blueprint, membership, curriculum, and community.',
  alternates: { canonical: '/about/faq' },
  openGraph: {
    title: 'Frequently Asked Questions | The DevSec Blueprint',
    description: 'Find answers to common questions about The DevSec Blueprint, membership, curriculum, and community.',
    url: '/about/faq',
  },
};

export default function FAQPage() {
  const allQuestions = FAQ_CATEGORIES.flatMap((cat) => cat.questions);

  const faqJsonLd =
    allQuestions.length > 0
      ? {
          '@context': 'https://schema.org',
          '@type': 'FAQPage',
          mainEntity: allQuestions.map((q) => ({
            '@type': 'Question',
            name: q.question,
            acceptedAnswer: {
              '@type': 'Answer',
              text: q.answer,
            },
          })),
        }
      : null;

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950">
      <NavbarWithAuth />

      <main className="pt-24 pb-12">
        {/* Page Header */}
        <section className="max-w-5xl mx-auto px-6 py-12 text-center">
          <p className="text-sm font-semibold uppercase tracking-wide text-primary-500 dark:text-primary-400">
            FAQ
          </p>
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-gray-100 mt-3">
            Frequently Asked Questions
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400 mt-4 max-w-2xl mx-auto">
            Find answers to common questions about The DevSec Blueprint, our curriculum, community, and how to get started.
          </p>
        </section>

        {/* JSON-LD Structured Data */}
        {faqJsonLd && (
          <script
            type="application/ld+json"
            dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
          />
        )}

        {/* FAQ Content (client component with accordion) */}
        <FAQClient />

        {/* Footer CTA */}
        <section className="max-w-3xl mx-auto px-6 py-12 text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            Still Have Questions?
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Can&apos;t find what you&apos;re looking for? Reach out to our team directly.
          </p>
          <Link
            href="/about/contact"
            className="inline-block px-6 py-3 rounded-lg bg-primary-500 hover:bg-primary-600 text-gray-900 font-semibold transition-colors"
          >
            Contact Us
          </Link>
        </section>
      </main>

      <Footer />
    </div>
  );
}
