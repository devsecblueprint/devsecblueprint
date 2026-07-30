import type { Metadata } from 'next';
import { NavbarWithAuth } from '@/components/layout/NavbarWithAuth';
import { Footer } from '@/components/layout/Footer';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import Link from 'next/link';
import React from 'react';

const TOPIC_ICONS: Record<string, React.ReactNode> = {
  'Cloud Security': (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
    </svg>
  ),
  'Infrastructure as Code': (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  ),
  'CI/CD Pipelines': (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  ),
  'Container Security': (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
    </svg>
  ),
  'Kubernetes Security': (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
    </svg>
  ),
  'Network Security': (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  'Application Security': (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  ),
  'Identity & Access Management': (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
    </svg>
  ),
  'Incident Response': (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
    </svg>
  ),
  'Threat Modeling': (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z" />
    </svg>
  ),
  'Compliance & Governance': (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
    </svg>
  ),
  'Secrets Management': (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
    </svg>
  ),
  'Cloud Logging, Detection, and Response': (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  ),
  'Software Supply Chain Security': (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
    </svg>
  ),
};

const DIFFERENTIATOR_ICONS: Record<string, React.ReactNode> = {
  'Engineering-First': (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  ),
  'Real Projects': (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
    </svg>
  ),
  'Built Through Real Systems': (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
    </svg>
  ),
  'Career-Ready Skills': (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  ),
  'Community-Driven': (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
    </svg>
  ),
  'An Accessible Starting Point': (
    <svg className="w-8 h-8 text-primary-500 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
};

export const metadata: Metadata = {
  title: 'About The DevSec Blueprint',
  description: 'Learn what The DevSec Blueprint is, why it exists, and how it teaches DevSecOps through real-world engineering.',
  alternates: { canonical: '/about' },
  openGraph: {
    title: 'About The DevSec Blueprint',
    description: 'Learn what The DevSec Blueprint is, why it exists, and how it teaches DevSecOps through real-world engineering.',
    url: '/about',
  },
};

const TOPICS = [
  { title: 'Cloud Security', description: 'Secure cloud infrastructure, identities, workloads, data, and services across AWS, Azure, and Google Cloud.' },
  { title: 'Infrastructure as Code', description: 'Build and govern infrastructure through secure automation, policy as code, testing, and repeatable deployment patterns.' },
  { title: 'CI/CD Pipelines', description: 'Design secure software delivery workflows with identity federation, scanning, policy enforcement, artifact controls, and deployment safeguards.' },
  { title: 'Container Security', description: 'Secure container images, registries, runtimes, dependencies, and deployment workflows.' },
  { title: 'Kubernetes Security', description: 'Secure Kubernetes identity, workloads, networking, admission controls, secrets, and runtime environments.' },
  { title: 'Network Security', description: 'Design and defend cloud, application, and hybrid network architectures using segmentation, private connectivity, and layered controls.' },
  { title: 'Application Security', description: 'Identify and reduce application risk through secure design, code analysis, dependency management, testing, and remediation.' },
  { title: 'Identity & Access Management', description: 'Design least-privilege access, federated identity, workload identity, role assumption, and short-lived authentication patterns.' },
  { title: 'Incident Response', description: 'Investigate, contain, respond to, and recover from security incidents across cloud and software delivery environments.' },
  { title: 'Threat Modeling', description: 'Identify assets, trust boundaries, attack paths, abuse cases, and security requirements before systems reach production.' },
  { title: 'Compliance & Governance', description: 'Translate organizational requirements into enforceable guardrails, policy-as-code controls, and measurable technical standards.' },
  { title: 'Secrets Management', description: 'Securely store, retrieve, rotate, and govern credentials, tokens, keys, and other sensitive configuration.' },
  { title: 'Cloud Logging, Detection, and Response', description: 'Turn cloud telemetry into tested detections, actionable findings, automated response workflows, and defensible evidence.' },
  { title: 'Software Supply Chain Security', description: 'Establish trust across source code, dependencies, build systems, artifacts, registries, and deployment environments.' },
];

const STEPS = [
  { number: 1, title: 'Learn the Foundation', description: 'Understand the concepts, terminology, security objectives, and threat landscape surrounding the system.' },
  { number: 2, title: 'Study the System', description: 'Examine the architecture, trust boundaries, dependencies, identities, data flows, and operational constraints.' },
  { number: 3, title: 'Build the Solution', description: 'Implement practical security controls, workflows, and projects using real technologies and engineering patterns.' },
  { number: 4, title: 'Test and Troubleshoot', description: 'Validate expected behavior, troubleshoot failures, test assumptions, and understand how controls behave when systems change.' },
  { number: 5, title: 'Document and Explain', description: 'Document architecture, implementation decisions, limitations, evidence, and results—because engineering is incomplete when the work cannot be understood or maintained by others.' },
];

const DIFFERENTIATORS = [
  { title: 'Engineering-First', description: 'We teach the principles, architectures, tradeoffs, and implementation patterns behind security—not merely how to operate individual tools.' },
  { title: 'Real Projects', description: 'Learners apply concepts through walkthroughs, guided projects, mini-capstones, and reference implementations that can become evidence of practical experience.' },
  { title: 'Built Through Real Systems', description: 'Concepts are taught in the context of cloud environments, delivery pipelines, infrastructure, identities, applications, containers, and operational workflows.' },
  { title: 'Career-Ready Skills', description: 'Develop the technical communication, project documentation, portfolio evidence, and career strategy needed to present your experience effectively.' },
  { title: 'Community-Driven', description: 'Learn alongside practitioners who build, contribute, review projects, share technical knowledge, and support one another through the process.' },
  { title: 'An Accessible Starting Point', description: 'DSB provides a public foundation for learning, with expanded walkthroughs, projects, reviews, community experiences, and structured guidance available through paid memberships.' },
];

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-white dark:bg-gray-950">
      <NavbarWithAuth />

      <main>
        {/* Page Header */}
        <section className="pt-24 pb-12 px-4 sm:px-6">
          <div className="max-w-4xl mx-auto text-center">
            <p className="text-sm font-semibold uppercase tracking-wider text-primary-500 dark:text-primary-400 mb-4">
              ABOUT THE DEVSEC BLUEPRINT
            </p>
            <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 dark:text-gray-100 mb-6">
              Building Security Engineers Through Real Systems
            </h1>
            <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
              The DevSec Blueprint is a structured learning platform for practical DevSecOps and cloud security education—built around real systems, guided projects, and engineering decisions rather than theory alone.
            </p>
          </div>
        </section>

        {/* Hero CTA Section */}
        <section className="pb-16 px-4 sm:px-6">
          <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/curriculum">
              <Button variant="primary" size="lg">
                View Curriculum
              </Button>
            </Link>
            <Link href="/pricing">
              <Button variant="secondary" size="lg">
                Compare Memberships
              </Button>
            </Link>
          </div>
        </section>

        {/* What The DevSec Blueprint Is */}
        <section className="py-16 px-4 sm:px-6 bg-gray-50 dark:bg-gray-900/50">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">
              What The DevSec Blueprint Is
            </h2>
            <p className="text-lg text-gray-700 dark:text-gray-300 mb-4">
              The DevSec Blueprint is a practical learning platform designed for professionals building skills across DevSecOps, cloud security, and modern security engineering.
            </p>
            <p className="text-lg text-gray-700 dark:text-gray-300 mb-6">
              DSB combines foundational curriculum, technical walkthroughs, guided projects, mini-capstones, reference implementations, and community support into structured learning experiences that reflect how security work is performed across real systems.
            </p>
            <div className="border-l-4 border-primary-400 dark:border-primary-500 pl-6 py-2">
              <p className="text-xl font-semibold text-gray-900 dark:text-gray-100 italic">
                &ldquo;Structured DevSecOps and cloud security mastery. Built through real systems, not theory.&rdquo;
              </p>
            </div>
          </div>
        </section>

        {/* Why DSB Exists */}
        <section className="py-16 px-4 sm:px-6">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">
              Why DSB Exists
            </h2>
            <p className="text-lg text-gray-700 dark:text-gray-300 mb-4">
              Security education often leaves a gap between understanding individual concepts and knowing how to apply them inside a complete system. Certifications can establish foundational knowledge, while tool-specific tutorials can demonstrate isolated tasks—but neither automatically teaches someone how to connect architecture, automation, security controls, troubleshooting, and technical communication.
            </p>
            <p className="text-lg text-gray-700 dark:text-gray-300 mb-4">
              DSB exists to help bridge that gap. We believe effective security engineers must understand how systems are built, operated, secured, and maintained.
            </p>
            <p className="text-lg text-gray-700 dark:text-gray-300">
              The platform provides structured learning paths, practical projects, technical guidance, and community support designed to help practitioners connect security concepts across real environments.
            </p>
          </div>
        </section>

        {/* What We Teach */}
        <section className="py-16 px-4 sm:px-6 bg-gray-50 dark:bg-gray-900/50">
          <div className="max-w-7xl mx-auto">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4 text-center">
              What We Teach
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-400 mb-10 text-center max-w-2xl mx-auto">
              Our curriculum spans the core disciplines required to build, secure, operate, and defend modern software delivery and cloud environments.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {TOPICS.map((topic) => (
                <Card key={topic.title} padding="md" className="hover:shadow-xl transition-shadow">
                  <div className="mb-3">
                    {TOPIC_ICONS[topic.title]}
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                    {topic.title}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {topic.description}
                  </p>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* How We Teach */}
        <section className="py-16 px-4 sm:px-6">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4 text-center">
              How We Teach
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-400 mb-10 text-center max-w-2xl mx-auto">
              DSB learning experiences are designed around a practical progression that moves learners from foundational understanding to implementation, validation, and technical communication.
            </p>
            <div className="space-y-8">
              {STEPS.map((step) => (
                <div key={step.number} className="flex gap-6 items-start">
                  <div className="flex-shrink-0 w-12 h-12 rounded-full bg-primary-400 dark:bg-primary-500 flex items-center justify-center">
                    <span className="text-lg font-bold text-gray-900">{step.number}</span>
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-1">
                      {step.title}
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400">
                      {step.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* What Makes DSB Different */}
        <section className="py-16 px-4 sm:px-6 bg-gray-50 dark:bg-gray-900/50">
          <div className="max-w-7xl mx-auto">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4 text-center">
              What Makes DSB Different
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {DIFFERENTIATORS.map((item) => (
                <Card key={item.title} padding="md" className="hover:shadow-xl transition-shadow">
                  <div className="mb-3">
                    {DIFFERENTIATOR_ICONS[item.title]}
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                    {item.title}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {item.description}
                  </p>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Built by Practitioners */}
        <section className="py-16 px-4 sm:px-6">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6 text-center">
              Built by Practitioners
            </h2>
            <p className="text-lg text-gray-700 dark:text-gray-300 mb-4">
              The DevSec Blueprint is built by security engineers, cloud practitioners, technical educators, contributors, and community members who understand the gap between learning isolated concepts and applying them inside real environments.
            </p>
            <p className="text-lg text-gray-700 dark:text-gray-300 mb-8">
              The platform is led by founder Damien Burks and supported by contributors who bring experience across cloud security, DevSecOps, software delivery, infrastructure automation, application security, and technical education.
            </p>
            <div className="flex justify-center">
              <Link href="/about/leadership">
                <Button variant="primary" size="lg">
                  Meet the DSB Leadership Team
                </Button>
              </Link>
            </div>
          </div>
        </section>

        {/* Mission Statement */}
        <section className="py-16 px-4 sm:px-6">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">
              Our Mission
            </h2>
            <p className="text-xl text-gray-700 dark:text-gray-300 leading-relaxed">
              To make practical DevSecOps and cloud security education more structured, accessible, and engineering-driven—empowering practitioners to build, secure, operate, and defend real production systems with confidence.
            </p>
          </div>
        </section>

        {/* Vision Statement */}
        <section className="py-16 px-4 sm:px-6 bg-gray-50 dark:bg-gray-900/50">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">
              Our Vision
            </h2>
            <p className="text-xl text-gray-700 dark:text-gray-300 leading-relaxed">
              A world where security is understood as a core engineering discipline—not an afterthought—and every practitioner has the opportunity to develop the skills required to build systems that are secure by design.
            </p>
          </div>
        </section>

        {/* Closing CTA */}
        <section className="py-20 px-4 sm:px-6">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4">
              Ready to Start Building?
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-400 mb-8">
              Explore the DSB curriculum, choose the learning experience that fits your goals, and begin building practical DevSecOps and cloud security experience through real systems.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/curriculum">
                <Button variant="primary" size="lg">
                  Explore the Curriculum
                </Button>
              </Link>
              <Link href="/pricing">
                <Button variant="secondary" size="lg">
                  Compare Memberships
                </Button>
              </Link>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
