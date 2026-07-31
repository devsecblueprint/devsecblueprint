/**
 * FAQ Data File
 *
 * Structured FAQ content for the About section FAQ page.
 * Slug constraints: lowercase, a-z/0-9/hyphens only, max 80 chars, starts with a letter.
 * Pattern: ^[a-z][a-z0-9-]{0,79}$
 */

export interface FAQQuestion {
  /** The question text */
  question: string;
  /** The answer text (can contain basic HTML/markdown) */
  answer: string;
  /** Lowercase, hyphen-separated slug for URL hash navigation. Pattern: ^[a-z][a-z0-9-]{0,79}$ */
  slug: string;
}

export interface FAQCategory {
  /** Display name for the category */
  name: string;
  /** Lowercase, hyphen-separated slug. Pattern: ^[a-z][a-z0-9-]{0,79}$ */
  slug: string;
  /** Array of FAQ questions in this category (1+ items) */
  questions: FAQQuestion[];
}

export const FAQ_CATEGORIES: FAQCategory[] = [
  {
    name: "About DSB",
    slug: "about-dsb",
    questions: [
      {
        question: "What is The DevSec Blueprint?",
        answer:
          "The DevSec Blueprint is a structured learning platform designed to help engineers learn DevSecOps and cloud security through real-world concepts, hands-on modules, and capstone projects. Instead of focusing only on tools, the platform focuses on the engineering principles behind secure software delivery.",
        slug: "what-is-the-devsec-blueprint",
      },
      {
        question: "Is The DevSec Blueprint free to use?",
        answer:
          "The DevSec Blueprint offers both free and paid content. Basic resources and community access are available at no cost, while full access to structured courses, capstone projects, and advanced modules requires a paid membership. Visit the pricing page to see available plans and find the right fit for your learning goals.",
        slug: "is-the-devsec-blueprint-free",
      },
      {
        question: "What makes DSB different from other platforms?",
        answer:
          "DSB focuses on engineering principles rather than just tool usage. The platform emphasizes building real projects, understanding system design, and developing security thinking. You learn by doing — building, testing, troubleshooting, and documenting solutions rather than passively watching videos.",
        slug: "what-makes-dsb-different",
      },
      {
        question: "What data does The DevSec Blueprint collect?",
        answer:
          "The DevSec Blueprint collects basic profile information from your authentication provider (username, name, profile icon) and course-related metrics such as module completion and quiz progress. If you decide you no longer want your information stored, you can delete your account at any time.",
        slug: "what-data-does-dsb-collect",
      },
    ],
  },
  {
    name: "Membership/Billing",
    slug: "membership-billing",
    questions: [
      {
        question: "How can I support The DevSec Blueprint?",
        answer:
          "The DevSec Blueprint offers paid membership plans that give you full access to courses, capstone projects, and community features. You can view available plans and pricing at /pricing. If you'd like to go further and support the project's growth, we also accept sponsorships through GitHub Sponsors at https://github.com/sponsors/devsecblueprint.",
        slug: "how-can-i-support-dsb",
      },
      {
        question: "What authentication providers are supported?",
        answer:
          "The platform currently supports authentication through GitHub, GitLab, and Bitbucket Cloud. Traditional username/password accounts are not used because capstone projects require submitting a Git repository, and maintaining a public repository is an important part of demonstrating your skills.",
        slug: "what-authentication-providers-are-supported",
      },
      {
        question: "Can I delete my account and data?",
        answer:
          "Yes. If you ever decide you no longer want your information stored on the platform, you can delete your account at any time. This will remove your associated data from the system, including progress tracking and quiz results.",
        slug: "can-i-delete-my-account",
      },
    ],
  },
  {
    name: "Curriculum",
    slug: "curriculum",
    questions: [
      {
        question: "How long does the program take to complete?",
        answer:
          "The DevSec Blueprint is designed to be completed with part-time study. Most learners finish the program in approximately 3 to 5 months, depending on how much time they dedicate each week. The learning path includes structured modules, quizzes, and capstone projects.",
        slug: "how-long-does-the-program-take",
      },
      {
        question: "Do I need prior experience before starting?",
        answer:
          "Not necessarily. However, there is a prerequisites section that outlines foundational knowledge to help you succeed, including basic programming knowledge, familiarity with Linux, and general understanding of software development or infrastructure concepts.",
        slug: "do-i-need-prior-experience",
      },
      {
        question: "Do I need a degree to get into DevSecOps?",
        answer:
          "No. You do not need a degree to get into DevSecOps. Most companies primarily care about hands-on experience, skills, and the ability to solve real problems. That said, a degree can help you stand out. Relevant degrees include B.S. in Computer Science, B.S. in Cybersecurity, M.S. in Cybersecurity, or M.S. in Computer Science.",
        slug: "do-i-need-a-degree",
      },
      {
        question: "Do I need to be a strong coder to be a DevSecOps engineer?",
        answer:
          "To an extent, yes. DevSecOps engineers often build automation, extend pipelines, and sometimes develop internal security tools. You don't need to be a full-time software engineer, but you should be comfortable with scripting languages such as Bash, PowerShell, or Python and understand basic programming concepts.",
        slug: "do-i-need-to-be-a-strong-coder",
      },
      {
        question: "Do I need to learn the cloud to get a job in DevSecOps?",
        answer:
          "You don't strictly have to, but it is highly recommended. Many modern applications run in the cloud, and understanding at least one cloud provider is extremely valuable. Popular options include AWS, Azure, and Google Cloud.",
        slug: "do-i-need-to-learn-the-cloud",
      },
    ],
  },
  {
    name: "Community/Discord",
    slug: "community-discord",
    questions: [
      {
        question: "Is there a community for DSB learners?",
        answer:
          "Yes. The DevSec Blueprint has an active Discord community where learners can ask questions, share progress, collaborate on projects, and connect with others on the same learning path. The community is open to all skill levels.",
        slug: "is-there-a-community",
      },
      {
        question: "How do I join the Discord server?",
        answer:
          "You can join the DSB Discord server through the invite link available on the platform. Once you join, introduce yourself in the welcome channel and explore the various topic-specific channels for discussions on DevSecOps, cloud security, and career development.",
        slug: "how-do-i-join-discord",
      },
      {
        question: "What kind of support can I get from the community?",
        answer:
          "The community provides peer support for technical questions, study group coordination, project feedback, career advice, and general encouragement. Community members and mentors actively help each other troubleshoot issues and share resources.",
        slug: "what-support-from-community",
      },
    ],
  },
  {
    name: "Projects/Reviews",
    slug: "projects-reviews",
    questions: [
      {
        question: "Do I receive a certificate after completing the program?",
        answer:
          "The DevSec Blueprint does not currently issue formal certificates. Instead, the platform focuses on helping you build tangible projects through capstone work that can be added to your Git repositories and professional portfolio. These real-world artifacts often carry more weight with employers.",
        slug: "do-i-receive-a-certificate",
      },
      {
        question: "How are capstone projects submitted and reviewed?",
        answer:
          "Capstone projects are submitted via a public Git repository. You build the project following the provided specifications, push it to your repository, and submit the link through the platform. Projects are reviewed based on completeness, security practices, and code quality.",
        slug: "how-are-capstone-projects-reviewed",
      },
      {
        question: "Can I use capstone projects in my professional portfolio?",
        answer:
          "Absolutely. Capstone projects are designed to be portfolio-worthy. They demonstrate real-world skills in DevSecOps, cloud security, and infrastructure automation. Many learners showcase these projects during job interviews and on their professional profiles.",
        slug: "can-i-use-projects-in-portfolio",
      },
    ],
  },
  {
    name: "Career Development",
    slug: "career-development",
    questions: [
      {
        question: "What roles can I pursue after completing the program?",
        answer:
          "After completing The DevSec Blueprint, you can pursue roles such as DevSecOps Engineer, Cloud Security Engineer, Platform Security Engineer, Site Reliability Engineer (SRE), and Security Automation Engineer. The skills you build are applicable across many security-focused engineering positions.",
        slug: "what-roles-can-i-pursue",
      },
      {
        question: "Does DSB help with job placement?",
        answer:
          "The DevSec Blueprint does not offer direct job placement services. However, the platform equips you with portfolio projects, hands-on skills, and community connections that strengthen your job applications. The Discord community also shares job postings and career advice.",
        slug: "does-dsb-help-with-job-placement",
      },
      {
        question: "What certifications complement the DSB curriculum?",
        answer:
          "Certifications that pair well with the DSB curriculum include AWS Solutions Architect Associate, Google Cloud Associate Cloud Engineer, CompTIA Security+, Certified Kubernetes Security Specialist (CKS), and HashiCorp Terraform Associate. These validate specific tool and platform knowledge alongside your hands-on project experience.",
        slug: "what-certifications-complement-dsb",
      },
    ],
  },
  {
    name: "Contributions/Partnerships",
    slug: "contributions-partnerships",
    questions: [
      {
        question: "How can I contribute to The DevSec Blueprint?",
        answer:
          "You can contribute by submitting pull requests to the open-source repositories, reporting bugs, improving documentation, creating educational content, or mentoring other learners in the community. Check the GitHub repositories for contribution guidelines and open issues.",
        slug: "how-can-i-contribute",
      },
      {
        question: "Does DSB accept partnership or sponsorship inquiries?",
        answer:
          "Yes. The DevSec Blueprint is open to partnerships with organizations that align with our mission of making DevSecOps education accessible. For partnership or sponsorship inquiries, please reach out through the contact page.",
        slug: "does-dsb-accept-partnerships",
      },
      {
        question: "Can I create content or teach on the platform?",
        answer:
          "We welcome contributions from experienced practitioners who want to share their knowledge. If you are interested in creating modules, writing guides, or mentoring learners, reach out through the contact page to discuss collaboration opportunities.",
        slug: "can-i-create-content",
      },
    ],
  },
];
