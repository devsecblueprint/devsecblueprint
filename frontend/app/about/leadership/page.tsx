import type { Metadata } from 'next';
import Image from 'next/image';
import Link from 'next/link';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { Footer } from '@/components/layout/Footer';
import { Card } from '@/components/ui/Card';
import { TEAM_MEMBERS, ADVISORS, CORE_TEAM, TeamMember } from '@/lib/data/leadership';
import { ExpandableBio } from '@/components/ui/ExpandableBio';

export const metadata: Metadata = {
  title: 'Leadership | The DevSec Blueprint',
  description: 'Meet the team behind The DevSec Blueprint and the leadership philosophy driving DevSecOps education.',
  alternates: { canonical: '/about/leadership' },
  openGraph: {
    title: 'Leadership | The DevSec Blueprint',
    description: 'Meet the team behind The DevSec Blueprint and the leadership philosophy driving DevSecOps education.',
    url: '/about/leadership',
  },
};

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((word) => word[0])
    .join('')
    .toUpperCase();
}

function FallbackAvatar({ name, size = 'md' }: { name: string; size?: 'lg' | 'md' }) {
  const initials = getInitials(name);
  const sizeClasses = size === 'lg' ? 'w-40 h-40 text-4xl' : 'w-24 h-24 text-xl';

  return (
    <div
      className={`${sizeClasses} rounded-full bg-primary-400 text-gray-900 flex items-center justify-center font-bold`}
      aria-hidden="true"
    >
      {initials}
    </div>
  );
}

function FounderCard({ member }: { member: TeamMember }) {
  const linkedIn = member.socialLinks?.find((link) => link.platform === 'linkedin');

  return (
    <Card padding="lg" className="flex flex-col md:flex-row gap-8 items-center md:items-start">
      {/* Founder Photo */}
      <div className="flex-shrink-0">
        {member.photoUrl ? (
          <Image
            src={member.photoUrl}
            alt={`${member.name}, ${member.role}`}
            width={160}
            height={160}
            className="rounded-full object-cover w-40 h-40"
          />
        ) : (
          <FallbackAvatar name={member.name} size="lg" />
        )}
      </div>

      {/* Founder Info */}
      <div className="flex-1 text-center md:text-left">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {member.name}
        </h2>
        <p className="text-primary-500 dark:text-primary-400 font-medium mt-1">
          {member.role}
        </p>
        <div className="mt-4">
          <ExpandableBio bio={member.bio} className="text-gray-700 dark:text-gray-300 leading-relaxed" />
        </div>

        {/* Highlights */}
        <div className="mt-4">
          <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide">
            Highlights
          </h3>
          <ul className="mt-2 space-y-2">
            {member.highlights.map((item) => (
              <li key={item} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                <svg className="w-4 h-4 text-primary-400 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
                </svg>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* LinkedIn Link */}
        {linkedIn && (
          <a
            href={linkedIn.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 mt-4 text-primary-500 dark:text-primary-400 hover:underline font-medium"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
            </svg>
            LinkedIn
          </a>
        )}
      </div>
    </Card>
  );
}

function TeamMemberCard({ member }: { member: TeamMember }) {
  const linkedIn = member.socialLinks?.find((link) => link.platform === 'linkedin');

  return (
    <div className="bg-gray-900 dark:bg-gray-900 border border-gray-800 rounded-xl p-6 sm:p-8">
      {/* Header — avatar + role + name */}
      <div className="flex items-center gap-4 mb-5">
        {member.photoUrl ? (
          <Image
            src={member.photoUrl}
            alt={`${member.name}, ${member.role}`}
            width={56}
            height={56}
            className="rounded-full object-cover w-14 h-14"
          />
        ) : (
          <div className="w-14 h-14 rounded-full bg-gray-700 text-gray-300 flex items-center justify-center font-bold text-lg flex-shrink-0" aria-hidden="true">
            {getInitials(member.name)}
          </div>
        )}
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-primary-400">
            {member.role}
          </p>
          <h3 className="text-lg font-bold text-gray-100">
            {member.name}
          </h3>
        </div>
      </div>

      {/* Bio */}
      <div className="mb-5">
        <ExpandableBio bio={member.bio} className="text-sm text-gray-300 leading-relaxed" />
      </div>

      {/* Highlights */}
      <ul className="space-y-2 mb-5">
        {member.highlights.map((item) => (
          <li key={item} className="flex items-start gap-2 text-sm text-gray-300">
            <span className="text-primary-400 mt-1 flex-shrink-0">•</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>

      {/* LinkedIn */}
      {linkedIn && (
        <a
          href={linkedIn.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 text-primary-400 hover:text-primary-300 text-sm font-medium transition-colors"
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
          </svg>
          Connect on LinkedIn
        </a>
      )}
    </div>
  );
}

export default function LeadershipPage() {
  const founder = TEAM_MEMBERS.find((m) => m.isFounder);
  const otherMembers = CORE_TEAM.filter((m) => !m.isFounder);

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950">
      <NavbarWithAuth />

      <main className="pt-24 pb-12">
        {/* Page Header */}
        <section className="max-w-5xl mx-auto px-6 py-12 text-center">
          <p className="text-sm font-semibold uppercase tracking-wide text-primary-500 dark:text-primary-400">
            Who We Are
          </p>
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-gray-100 mt-3">
            Meet Our Leadership Team
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400 mt-4 max-w-2xl mx-auto">
            The people driving DevSecOps education forward through real-world engineering and community-first leadership.
          </p>
        </section>

        {/* Founder — featured at top */}
        {founder && (
          <section className="max-w-4xl mx-auto px-6 py-8">
            <FounderCard member={founder} />
          </section>
        )}

        {/* Other Leadership Members */}
        {otherMembers.length > 0 && (
          <section className="max-w-5xl mx-auto px-6 py-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {otherMembers.map((member) => (
                <TeamMemberCard key={member.name} member={member} />
              ))}
            </div>
          </section>
        )}

        {/* Leadership Philosophy */}
        <section className="max-w-4xl mx-auto px-6 py-12">
          <Card padding="lg" className="text-center">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
              Our Leadership Philosophy
            </h2>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              We believe that the best way to learn security is by building real systems and breaking them safely.
              Our leadership philosophy centers on transparency, hands-on mentorship, and community-driven growth.
              Every decision we make is guided by one question: does this help engineers become more capable
              and confident in securing the software they build?
            </p>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed mt-4">
              We lead by example — shipping open-source projects, sharing failures alongside successes,
              and creating space for engineers at every level to contribute, learn, and grow together.
            </p>
          </Card>
        </section>

        {/* Advisors Section (conditional) */}
        {ADVISORS.length > 0 && (
          <section className="max-w-5xl mx-auto px-6 py-12">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 text-center mb-8">
              Advisors
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {ADVISORS.map((advisor) => (
                <TeamMemberCard key={advisor.name} member={advisor} />
              ))}
            </div>
          </section>
        )}

        {/* Closing CTA */}
        <section className="max-w-3xl mx-auto px-6 py-12 text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            Want to Connect?
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Get in touch with our team to ask questions, explore partnerships, or just say hello.
          </p>
          <Link
            href="/about/contact"
            className="inline-block px-6 py-3 rounded-lg bg-primary-500 hover:bg-primary-600 text-gray-900 font-semibold transition-colors"
          >
            Get in Touch
          </Link>
        </section>
      </main>

      <Footer />
    </div>
  );
}
