import type { Metadata } from 'next';
import Image from 'next/image';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { Footer } from '@/components/layout/Footer';
import { Card } from '@/components/ui/Card';
import { ScrollButton } from '@/components/ui/ScrollButton';
import { SponsorshipFAQ } from '@/components/ui/SponsorshipFAQ';
import { SponsorshipInquiryForm } from '@/components/ui/SponsorshipInquiryForm';
import {
  COMMUNITY_METRICS,
  AUDIENCE_SEGMENTS,
  SPONSORSHIP_OPPORTUNITIES,
  WHY_PARTNER_BENEFITS,
  SPONSORSHIP_PRINCIPLES,
} from '@/lib/data/sponsorship-data';
import { PARTNERS } from '@/lib/data/partners';

const METRIC_ICONS: Record<string, React.ReactNode> = {
  "LinkedIn Followers": (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="currentColor">
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
    </svg>
  ),
  "Registered Platform Users": (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
    </svg>
  ),
  "Countries Represented": (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  "Organic Impressions": (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      <path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
  ),
  "Unique Organic Impressions": (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
  ),
  "Clicks and Social Engagements": (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
    </svg>
  ),
};

const AUDIENCE_ICONS: Record<string, React.ReactNode> = {
  "DevSecOps Engineers": (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  ),
  "Cloud Security Practitioners": (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
    </svg>
  ),
  "Security Engineers": (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
    </svg>
  ),
  "Developers and Platform Engineers": (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
    </svg>
  ),
  "Emerging Technical Talent": (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 14l9-5-9-5-9 5 9 5z" />
      <path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
      <path d="M12 14l-9-5" />
    </svg>
  ),
  "Technical Leaders and Hiring Teams": (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  ),
};

const BENEFIT_ICONS: Record<string, React.ReactNode> = {
  "A Focused Technical Audience": (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
    </svg>
  ),
  "Learning Through Real Systems": (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
    </svg>
  ),
  "Community Trust": (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
    </svg>
  ),
  "Meaningful Community Impact": (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3" />
    </svg>
  ),
};

const PRINCIPLE_ICONS: Record<string, React.ReactNode> = {
  "Technical Independence": (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
    </svg>
  ),
  "Clear Disclosure": (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      <path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
  ),
  "Educational Value": (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
    </svg>
  ),
  "Audience Relevance": (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
    </svg>
  ),
  "Editorial Control": (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
    </svg>
  ),
  "Limited Sponsorship Inventory": (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
    </svg>
  ),
};

export const metadata: Metadata = {
  title: 'Sponsorships | The DevSec Blueprint',
  description: 'Explore sponsorship opportunities with The DevSec Blueprint. Partner with a growing global community of DevSecOps and cloud security practitioners.',
  alternates: { canonical: '/sponsorships' },
  openGraph: {
    title: 'Sponsorships | The DevSec Blueprint',
    description: 'Explore sponsorship opportunities with The DevSec Blueprint. Partner with a growing global community of DevSecOps and cloud security practitioners.',
    url: '/sponsorships',
  },
};

export default function SponsorshipsPage() {
  return (
    <div className="min-h-screen bg-white dark:bg-gray-950">
      <NavbarWithAuth />

      <main>
        {/* Hero Section */}
        <section className="pt-24 pb-12 px-4 sm:px-6">
          <div className="max-w-4xl mx-auto text-center">
            <p className="text-sm font-semibold uppercase tracking-wider text-primary-500 dark:text-primary-400 mb-4">
              PARTNER WITH THE DEVSEC BLUEPRINT
            </p>
            <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 dark:text-gray-100 mb-6">
              Sponsor the Future of Practical Security Engineering
            </h1>
            <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto mb-4">
              The DevSec Blueprint is building the next generation of security engineers through hands-on, project-based education. Your sponsorship directly funds scholarships, platform development, and accessible content for a global technical community.
            </p>
            <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto mb-8">
              Join us as a founding partner and connect your brand with practitioners who are actively building, learning, and shaping the future of DevSecOps.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <ScrollButton targetId="founding-sponsor" variant="primary" size="lg">
                Become a Founding Sponsor
              </ScrollButton>
              <ScrollButton targetId="sponsorship-opportunities" variant="secondary" size="lg">
                Explore Sponsorship Opportunities
              </ScrollButton>
            </div>
          </div>
        </section>

        {/* Metrics Section */}
        <section className="py-16 px-4 sm:px-6">
          <div className="max-w-7xl mx-auto">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4 text-center">
              A Growing Global Technical Community
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-10">
              {COMMUNITY_METRICS.map((metric) => (
                <Card key={metric.label} padding="md" className="text-center">
                  <div className="flex justify-center mb-3">
                    {METRIC_ICONS[metric.label]}
                  </div>
                  <p className="text-3xl font-bold text-primary-500 dark:text-primary-400 mb-1">
                    {metric.value}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {metric.label}
                  </p>
                </Card>
              ))}
            </div>
            <p className="text-center text-lg font-semibold text-gray-700 dark:text-gray-300 mt-8">
              ~4% organic engagement rate
            </p>
            <div className="mt-6 space-y-2 text-center">
              <p className="text-xs text-gray-500 dark:text-gray-500">
                Website analytics sourced from Google Analytics for January through July 2026.
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500">
                LinkedIn data reflects a two-week measurement period with no paid promotion.
              </p>
            </div>
          </div>
        </section>

        {/* Partners Section - conditionally rendered */}
        {PARTNERS.length > 0 && (
          <section className="py-16 px-4 sm:px-6 bg-gray-50 dark:bg-gray-900/50">
            <div className="max-w-7xl mx-auto">
              <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4 text-center">
                Community Partners
              </h2>
              <p className="text-lg text-gray-600 dark:text-gray-400 mb-10 text-center max-w-2xl mx-auto">
                These organizations support The DevSec Blueprint&apos;s mission to make security engineering education accessible to a global audience.
              </p>
              <div className={`grid gap-8 max-w-5xl mx-auto ${PARTNERS.length === 1 ? 'grid-cols-1 max-w-sm' : PARTNERS.length === 2 ? 'grid-cols-1 sm:grid-cols-2 max-w-3xl' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'}`}>
                {PARTNERS.map((partner) => {
                  const logoElement = partner.logoPath.endsWith('.svg') ? (
                    <img
                      src={partner.logoPath}
                      alt={`${partner.name} logo`}
                      className="w-full h-full object-contain"
                    />
                  ) : (
                    <Image
                      src={partner.logoPath}
                      alt={`${partner.name} logo`}
                      width={600}
                      height={400}
                      className="w-full h-full object-contain"
                    />
                  );

                  const cardContent = (
                    <div className="relative group flex items-center justify-center rounded-lg border border-gray-200 dark:border-gray-800 overflow-hidden aspect-square">
                      {logoElement}
                      <div className="absolute inset-0 flex items-center justify-center bg-gray-900/70 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg">
                        <span className="text-white font-semibold text-base text-center px-4">
                          {partner.name}
                        </span>
                      </div>
                    </div>
                  );

                  return partner.url ? (
                    <a key={partner.name} href={partner.url} target="_blank" rel="noopener noreferrer" title={partner.name}>
                      {cardContent}
                    </a>
                  ) : (
                    <div key={partner.name}>
                      {cardContent}
                    </div>
                  );
                })}
              </div>
            </div>
          </section>
        )}

        {/* Audience Section */}
        <section className="py-16 px-4 sm:px-6 bg-gray-50 dark:bg-gray-900/50">
          <div className="max-w-7xl mx-auto">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-10 text-center">
              Who You Reach
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {AUDIENCE_SEGMENTS.map((segment) => (
                <Card key={segment.title} padding="md">
                  <div className="mb-3">
                    {AUDIENCE_ICONS[segment.title]}
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                    {segment.title}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {segment.description}
                  </p>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Opportunities Section */}
        <section id="sponsorship-opportunities" className="py-16 px-4 sm:px-6">
          <div className="max-w-7xl mx-auto">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-10 text-center">
              Sponsorship Opportunities
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {SPONSORSHIP_OPPORTUNITIES.map((opportunity) => (
                <Card key={opportunity.title} padding="md">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
                    {opportunity.title}
                  </h3>
                  <ul className="space-y-2">
                    {opportunity.benefits.map((benefit) => (
                      <li key={benefit} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                        <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-primary-400 dark:bg-primary-500" aria-hidden="true" />
                        {benefit}
                      </li>
                    ))}
                  </ul>
                </Card>
              ))}
            </div>
            <p className="text-center text-gray-600 dark:text-gray-400 mt-8 max-w-2xl mx-auto">
              All sponsorship packages are custom-developed around your organizational goals. Reach out to discuss how we can build a partnership that delivers value for your team and our community.
            </p>
          </div>
        </section>

        {/* Benefits Section */}
        <section className="py-16 px-4 sm:px-6 bg-gray-50 dark:bg-gray-900/50">
          <div className="max-w-7xl mx-auto">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-10 text-center">
              Why Partner With Us
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {WHY_PARTNER_BENEFITS.map((benefit) => (
                <Card key={benefit.title} padding="md">
                  <div className="mb-3">
                    {BENEFIT_ICONS[benefit.title]}
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                    {benefit.title}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {benefit.description}
                  </p>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Principles Section */}
        <section className="py-16 px-4 sm:px-6 bg-gray-50 dark:bg-gray-900/50">
          <div className="max-w-7xl mx-auto">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-10 text-center">
              Our Sponsorship Principles
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {SPONSORSHIP_PRINCIPLES.map((principle) => (
                <Card key={principle.title} padding="md">
                  <div className="mb-3">
                    {PRINCIPLE_ICONS[principle.title]}
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                    {principle.title}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {principle.description}
                  </p>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Founding CTA Section */}
        <section id="founding-sponsor" className="py-16 px-4 sm:px-6 bg-gray-50 dark:bg-gray-900/50">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">
              Become a Founding Sponsor
            </h2>
            <p className="text-lg text-gray-700 dark:text-gray-300 mb-4">
              Founding sponsors receive permanent recognition across the platform and direct input into community initiatives. This is a limited opportunity to shape the future of security education alongside a dedicated engineering community.
            </p>
            <p className="text-lg text-gray-700 dark:text-gray-300 mb-8">
              Your support funds scholarships for underrepresented learners, new curriculum development, and platform features that make hands-on security education accessible worldwide.
            </p>
            <ScrollButton targetId="sponsorship-inquiry" variant="primary" size="lg">
              Start a Sponsorship Conversation
            </ScrollButton>
          </div>
        </section>

        {/* FAQ Section */}
        <section className="py-16 px-4 sm:px-6">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-10 text-center">
              Frequently Asked Questions
            </h2>
            <SponsorshipFAQ />
          </div>
        </section>

        {/* Inquiry Form Section */}
        <section id="sponsorship-inquiry" className="py-16 px-4 sm:px-6 bg-gray-50 dark:bg-gray-900/50">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-10 text-center">
              Ready to Partner?
            </h2>
            <SponsorshipInquiryForm />
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
