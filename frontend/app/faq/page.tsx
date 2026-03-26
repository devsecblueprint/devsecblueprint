"use client";

import React from "react";
import { NavbarWithAuth } from "@/components/layout/NavbarWithAuth";
import { Footer } from "@/components/layout/Footer";

export default function FAQPage() {
  return (
    <div className="min-h-screen bg-white dark:bg-gray-950">
      {/* Navbar */}
      <NavbarWithAuth />

      {/* Main Content */}
      <div className="bg-gray-50 dark:bg-gray-900 pt-24 pb-12">
        <div className="max-w-4xl mx-auto px-6 py-12">
          {/* Header */}
          <div className="mb-12">
            <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4">
              FAQ
            </h1>
            <p className="text-lg text-gray-600 dark:text-gray-400">
              Frequently Asked Questions
            </p>
          </div>

          {/* Content */}
          <div className="prose prose-lg dark:prose-invert max-w-none">
            <p className="text-gray-700 dark:text-gray-300 mb-8">
              This page contains a list of frequently asked questions and some
              answers from us.
            </p>

            {/* Question 1 */}
            <section className="mb-10">
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                What is The DevSec Blueprint?
              </h2>
              <p className="text-gray-700 dark:text-gray-300 mb-4">
                The DevSec Blueprint is a structured learning platform designed
                to help engineers learn DevSecOps and cloud security through
                real-world concepts, hands-on modules, and capstone projects.
              </p>
              <p className="text-gray-700 dark:text-gray-300">
                Instead of focusing only on tools, the platform focuses on the
                engineering principles behind secure software delivery. By the
                end of the learning path, you should have a stronger
                understanding of DevSecOps practices and tangible projects that
                demonstrate your skills.
              </p>
            </section>

            {/* Question 2 */}
            <section className="mb-10">
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Is The DevSec Blueprint free to use?
              </h2>
              <p className="text-gray-700 dark:text-gray-300 mb-4">
                Yes. The DevSec Blueprint is an open learning platform designed
                to make DevSecOps education more accessible. Anyone can use the
                platform to learn DevSecOps concepts and build real-world
                security skills.
              </p>

              <p className="text-gray-700 dark:text-gray-300">
                If you find value in the platform and would like to support the
                project, we accept sponsorships to help cover infrastructure and
                operational costs for running and maintaining the platform. You
                can support the project through GitHub Sponsors here:
              </p>

              <p className="text-gray-700 dark:text-gray-300 mt-2">
                <a
                  href="https://github.com/sponsors/devsecblueprint"
                  className="text-blue-600 dark:text-blue-400 underline"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  https://github.com/sponsors/devsecblueprint
                </a>
              </p>
            </section>

            {/* Question 3 */}
            <section className="mb-10">
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                How long does the program take to complete?
              </h2>
              <p className="text-gray-700 dark:text-gray-300">
                The DevSec Blueprint is designed to be completed with part-time
                study. Most learners finish the program in approximately{" "}
                <strong>3 to 5 months</strong>, depending on how much time they
                dedicate each week. The learning path includes structured
                modules, quizzes, and capstone projects that require you to
                build and submit tangible work.
              </p>
            </section>

            {/* Question 4 */}
            <section className="mb-10">
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Do I need prior experience before starting?
              </h2>
              <p className="text-gray-700 dark:text-gray-300">
                Not necessarily. However, we do provide a prerequisites section
                that outlines the foundational knowledge that will help you
                succeed in the program. This includes basic programming
                knowledge, familiarity with Linux, and general understanding of
                software development or infrastructure concepts.
              </p>
            </section>

            {/* Question 5 */}
            <section className="mb-10">
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Do I need a degree to get into DevSecOps?
              </h2>
              <p className="text-gray-700 dark:text-gray-300 mb-4">
                No. You do not need a degree to get into DevSecOps. Most
                companies primarily care about hands-on experience, skills, and
                the ability to solve real problems.
              </p>
              <p className="text-gray-700 dark:text-gray-300 mb-4">
                That said, a degree can help you stand out and provide a strong
                theoretical foundation. Some degrees that align well with
                DevSecOps include:
              </p>
              <ol className="list-decimal list-inside space-y-2 text-gray-700 dark:text-gray-300">
                <li>
                  B.S. in Computer Science (with a Cybersecurity focus if
                  possible)
                </li>
                <li>B.S. in Cybersecurity</li>
                <li>M.S. in Cybersecurity</li>
                <li>M.S. in Computer Science</li>
              </ol>
            </section>

            {/* Question 6 */}
            <section className="mb-10">
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Do I need to be a strong coder in order to be a DevSecOps
                engineer?
              </h2>
              <p className="text-gray-700 dark:text-gray-300 mb-4">
                To an extent, yes. DevSecOps engineers often build automation,
                extend pipelines, and sometimes develop internal security tools.
              </p>
              <p className="text-gray-700 dark:text-gray-300">
                You don't necessarily need to be a full-time software engineer,
                but you should be comfortable with scripting languages such as
                Bash, PowerShell, or Python and understand basic programming
                concepts.
              </p>
            </section>

            {/* Question 7 */}
            <section className="mb-10">
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Do I need to learn the cloud to get a job in DevSecOps?
              </h2>
              <p className="text-gray-700 dark:text-gray-300 mb-4">
                You don't strictly have to, but it is highly recommended. Many
                modern applications run in the cloud, and understanding at least
                one cloud provider will be extremely valuable.
              </p>
              <p className="text-gray-700 dark:text-gray-300">
                Popular options include AWS, Azure, and Google Cloud.
                Certifications such as the AWS Solutions Architect Associate or
                Google Cloud Associate Cloud Engineer are good starting points.
              </p>
            </section>

            {/* Question 8 */}
            <section className="mb-10">
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Do I receive a certificate after completing the program?
              </h2>
              <p className="text-gray-700 dark:text-gray-300 mb-4">
                The DevSec Blueprint does not currently issue formal
                certificates.
              </p>
              <p className="text-gray-700 dark:text-gray-300">
                Instead, the platform focuses on helping you build tangible
                projects through capstone work that can be added to your Git
                repositories and professional portfolio. These real-world
                artifacts often carry more weight with employers than a
                traditional certificate.
              </p>
            </section>

            {/* Question 9 */}
            <section className="mb-10">
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                What authentication providers are supported?
              </h2>
              <p className="text-gray-700 dark:text-gray-300 mb-4">
                The platform currently supports authentication through GitHub
                and GitLab. We may add support for additional providers such as
                Bitbucket Cloud in the future.
              </p>
              <p className="text-gray-700 dark:text-gray-300">
                The platform avoids traditional username/password accounts
                because capstone projects require submitting a Git repository
                before they can be marked complete. As an engineer, maintaining
                a public repository for your work is an important part of
                demonstrating your skills.
              </p>
            </section>

            {/* Question 10 */}
            <section className="mb-10">
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                What data does The DevSec Blueprint collect?
              </h2>
              <p className="text-gray-700 dark:text-gray-300 mb-4">
                The DevSec Blueprint collects a small amount of information in
                order to provide platform features such as progress tracking,
                quizzes, and capstone submissions.
              </p>

              <p className="text-gray-700 dark:text-gray-300 mb-4">
                When you authenticate using GitHub, the platform may store basic
                profile information provided by GitHub such as your username,
                name, and profile icon. We also collect course-related metrics
                such as module completion and quiz progress so that the platform
                can track your learning progress.
              </p>

              <p className="text-gray-700 dark:text-gray-300">
                If you ever decide you no longer want your information stored on
                the platform, you can delete your account at any time, which
                will remove your associated data from the system.
              </p>
            </section>

            {/* Question 11 */}
            <section className="mb-10">
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                How can I support The DevSec Blueprint?
              </h2>
              <p className="text-gray-700 dark:text-gray-300 mb-4">
                If you find value in the platform and want to support continued
                development, you can sponsor the project on GitHub.
              </p>
              <p className="text-gray-700 dark:text-gray-300">
                <a
                  href="https://github.com/sponsors/devsecblueprint"
                  className="text-blue-600 dark:text-blue-400 underline"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  https://github.com/sponsors/devsecblueprint
                </a>
              </p>
            </section>
          </div>
        </div>
      </div>

      {/* Footer */}
      <Footer />
    </div>
  );
}
