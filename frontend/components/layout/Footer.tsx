import React from 'react';
import { POLICY_LINKS } from '@/lib/data/policies';
import { SOCIAL_LINKS } from '@/lib/data/socials';
import { SocialIcon } from '@/components/ui/SocialIcon';

export interface FooterProps {
  variant?: 'default' | 'minimal';
}

export function Footer({ variant = 'default' }: FooterProps) {
  const currentYear = new Date().getFullYear();

  if (variant === 'minimal') {
    return (
      <footer className="bg-gray-950 border-t border-gray-800 py-6">
        <div className="max-w-7xl mx-auto px-6">
          <p className="text-center text-sm text-gray-400">
            © {currentYear} The DevSec Blueprint. All rights reserved.
          </p>
        </div>
      </footer>
    );
  }

  return (
    <footer className="bg-gray-950 border-t border-gray-800 py-12">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand Section */}
          <div>
            <h3 className="text-lg font-semibold text-gray-100 mb-4">
              The DevSec Blueprint
            </h3>
            <p className="text-sm text-gray-400">
              Structured DevSecOps and Cloud Security mastery. Built through real systems, not theory.
            </p>
          </div>

          {/* Social Links */}
          <div>
            <h4 className="text-sm font-semibold text-gray-100 uppercase tracking-wide mb-4">
              Connect
            </h4>
            <ul className="space-y-3">
              {SOCIAL_LINKS.map((social) => (
                <li key={social.label}>
                  <a
                    href={social.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center space-x-2 text-sm text-gray-400 hover:text-[#ffbe00] transition-colors focus:outline-none focus:ring-2 focus:ring-primary-400 rounded py-2 min-h-[44px]"
                    aria-label={`Visit our ${social.label}`}
                  >
                    <SocialIcon icon={social.icon} />
                    <span>{social.label}</span>
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Support Links */}
          <div>
            <h4 className="text-sm font-semibold text-gray-100 uppercase tracking-wide mb-4">
              Support
            </h4>
            <ul className="space-y-3">
              <li>
                <a
                  href="/sponsorships"
                  className="flex items-center space-x-2 text-sm text-gray-400 hover:text-[#ffbe00] transition-colors focus:outline-none focus:ring-2 focus:ring-primary-400 rounded py-2 min-h-[44px]"
                  aria-label="Sponsorship opportunities"
                >
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                  </svg>
                  <span>Sponsors</span>
                </a>
              </li>
              <li>
                <a
                  href="/about/contact"
                  className="flex items-center space-x-2 text-sm text-gray-400 hover:text-[#ffbe00] transition-colors focus:outline-none focus:ring-2 focus:ring-primary-400 rounded py-2 min-h-[44px]"
                  aria-label="Contact us"
                >
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  <span>Contact Us</span>
                </a>
              </li>
            </ul>
          </div>

          {/* Legal Links */}
          <div>
            <h4 className="text-sm font-semibold text-gray-100 uppercase tracking-wide mb-4">
              Legal
            </h4>
            <ul className="space-y-3">
              {POLICY_LINKS.map((policy) => (
                <li key={policy.label}>
                  <a
                    href={policy.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-gray-400 hover:text-[#ffbe00] transition-colors focus:outline-none focus:ring-2 focus:ring-primary-400 rounded py-2 min-h-[44px] inline-block"
                  >
                    {policy.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Copyright Notice */}
        <div className="pt-8 border-t border-gray-800">
          <p className="text-center text-sm text-gray-400">
            © {currentYear} The DevSec Blueprint. All rights reserved.
          </p>
          <p className="text-center text-xs text-gray-500 mt-3">
            Built with care for the security engineering community. Powered by AWS.
          </p>
        </div>
      </div>
    </footer>
  );
}
