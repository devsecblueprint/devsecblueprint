/**
 * FAQ Data File
 *
 * Public-facing FAQ content for The DevSec Blueprint.
 * Slug constraints: lowercase, a-z/0-9/hyphens only, max 80 chars, starts with a letter.
 * Pattern: ^[a-z][a-z0-9-]{0,79}$
 */

export interface CrossLink {
  /** Display text for the link */
  text: string;
  /** URL or path the link points to */
  href: string;
  /** Whether the link opens in a new tab (external site) */
  external?: boolean;
}

export interface FAQQuestion {
  /** The question text */
  question: string;
  /** The answer text (can contain basic HTML/markdown) */
  answer: string;
  /** Lowercase, hyphen-separated slug for URL hash navigation */
  slug: string;
  /** Optional cross-links related to this question */
  links?: CrossLink[];
}

export interface FAQCategory {
  /** Display name for the category */
  name: string;
  /** Lowercase, hyphen-separated slug */
  slug: string;
  /** Short description of the category (max 120 chars) */
  description: string;
  /** Icon identifier for the category card */
  icon: string;
  /** Array of FAQ questions in this category */
  questions: FAQQuestion[];
}

export const FAQ_CATEGORIES: FAQCategory[] = [
  {
    name: "General",
    slug: "general",
    description: "Learn what DSB is, who it serves, and how our platform and community help engineers grow.",
    icon: "info-circle",
    questions: [
      {
        question: "What is The DevSec Blueprint?",
        answer:
          "The DevSec Blueprint (DSB) is a community-driven learning platform for DevSecOps, Cloud Security, and Security Engineering. We help members build practical skills through structured learning paths, guided walkthroughs, hands-on projects, mini-capstones, career resources, and opportunities to learn alongside other engineers. Our goal is not simply to help you consume content. We want to help you understand the work, build it yourself, and develop the confidence to apply it in real environments.",
        slug: "what-is-the-devsec-blueprint",
        links: [{ text: "Learn more about DSB", href: "/about" }],
      },
      {
        question: "Who is The DevSec Blueprint for?",
        answer:
          "DSB is built for aspiring and experienced engineers who want to grow in DevSecOps, Cloud Security, and related security-engineering disciplines. That includes career changers, students, developers, cloud and platform engineers, IT professionals, security practitioners, and experienced engineers expanding into a new area. You do not need to have everything figured out before joining. We provide a structured place to begin and a community to grow with.",
        slug: "who-is-dsb-for",
      },
      {
        question: "What makes DSB different from other learning platforms?",
        answer:
          "DSB combines structured education with real-world engineering practice and community support. Instead of centering the experience on passive video consumption or isolated tool tutorials, we teach members how technologies, security controls, infrastructure, automation, and delivery practices work together. Members build projects, complete capstones, participate in live programming, access career-development resources, and learn in a community where questions, collaboration, and progress are encouraged.",
        slug: "what-makes-dsb-different",
      },
      {
        question: "Is The DevSec Blueprint free?",
        answer:
          "Yes. DSB offers a free membership that gives you access to selected learning resources and the broader community experience. DSB Builder is our paid membership for members who want full access to premium walkthroughs, structured learning tracks, capstones, Builder programming, career-development resources, and private Builder community spaces.",
        slug: "is-dsb-free",
        links: [{ text: "Compare membership options", href: "/pricing" }],
      },
      {
        question: "Who created The DevSec Blueprint?",
        answer:
          "DSB was founded by Damien Burks and is supported by a growing leadership team, contributors, community advocates, and partners who care about helping people build meaningful careers in technology. The platform is shaped by practitioners with experience across cloud engineering, security, DevOps, education, mentorship, and workforce development.",
        slug: "who-created-dsb",
        links: [{ text: "Meet the leadership team", href: "/about/leadership" }],
      },
      {
        question: "How do I get started?",
        answer:
          "Create a DSB account, explore the public curriculum, and choose the membership that fits your goals. Builder members are guided through the Builder Journey, beginning with account setup, community connection, and the Prerequisites section before moving into a specialized engineering path. You can move at your own pace, and you will always have a clear next step.",
        slug: "how-do-i-get-started",
        links: [
          { text: "Explore the curriculum", href: "/curriculum" },
          { text: "View membership options", href: "/pricing" },
        ],
      },
    ],
  },
  {
    name: "Learning Experience",
    slug: "learning-experience",
    description: "Understand how the curriculum, prerequisites, walkthroughs, projects, and capstones work together.",
    icon: "book-open",
    questions: [
      {
        question: "How is the curriculum structured?",
        answer:
          "The curriculum is organized into progressive learning paths. Members begin with foundational prerequisites, then move into DevSecOps, Cloud Security, Security Engineering, and other specialized areas. Lessons, quizzes, walkthroughs, projects, and capstones are designed to build on one another so that you are not learning disconnected tools without understanding how they fit into the larger engineering process.",
        slug: "how-is-curriculum-structured",
        links: [{ text: "Explore the curriculum", href: "/curriculum" }],
      },
      {
        question: "Do I need prior experience before starting?",
        answer:
          "No specific job title, degree, or certification is required. Some familiarity with technology will help, but the Prerequisites section is designed to help members strengthen the foundations needed for the rest of the platform. You should be willing to work with the command line, source control, cloud platforms, scripting, and infrastructure concepts as you progress.",
        slug: "do-i-need-prior-experience",
      },
      {
        question: "What should I complete first?",
        answer:
          "Builder members should begin with the Prerequisites section. It establishes the shared technical foundation needed to get the most from the advanced learning paths, walkthroughs, and capstones. The Builder Journey will guide you through this sequence and help you understand what to work on next.",
        slug: "what-should-i-complete-first",
      },
      {
        question: "What is a guided walkthrough?",
        answer:
          "A guided walkthrough is a detailed, hands-on learning experience that helps you build or secure a realistic system step by step. Walkthroughs explain the decisions behind the implementation, not just the commands to run. The goal is for you to understand the architecture, security considerations, tradeoffs, and operational impact of what you are building.",
        slug: "what-is-a-guided-walkthrough",
      },
      {
        question: "What are mini-capstones and capstone projects?",
        answer:
          "Mini-capstones and capstone projects give you an opportunity to apply what you learned with less step-by-step guidance. Mini-capstones reinforce a focused set of skills, while larger capstones bring multiple concepts together in a realistic engineering scenario. They are designed to help you practice problem-solving, document your decisions, and create evidence of your technical growth.",
        slug: "what-are-capstones",
      },
      {
        question: "How are capstone projects submitted and reviewed?",
        answer:
          "Capstones are submitted through the DSB platform using the required repository or project information. Reviews focus on whether the submission was completed, how the solution was approached, the quality of the implementation and documentation, and whether the expected security and engineering concepts were demonstrated. The review process is intended to help members improve—not to punish them for learning in public.",
        slug: "how-are-capstones-reviewed",
      },
      {
        question: "Can I use DSB projects in my portfolio?",
        answer:
          "Yes, when the project instructions and applicable DSB license allow it. We encourage members to document what they built, explain the decisions they made, and be prepared to discuss the work in interviews. Your portfolio should reflect your own implementation and understanding rather than simply reproducing protected DSB content.",
        slug: "can-i-use-dsb-projects-in-portfolio",
      },
      {
        question: "How long does it take to complete the curriculum?",
        answer:
          "There is no single completion timeline because DSB is an evolving platform rather than a fixed bootcamp. Your pace will depend on your experience, schedule, and chosen learning path. Most new Builder members should focus first on completing the guided Builder Journey during their first 60 days, then continue progressing through the curriculum at a sustainable pace.",
        slug: "how-long-does-curriculum-take",
      },
    ],
  },
  {
    name: "Builder Membership",
    slug: "builder-membership",
    description: "See what Builder includes and how the guided membership experience supports your growth.",
    icon: "star",
    questions: [
      {
        question: "What is DSB Builder?",
        answer:
          "DSB Builder is the paid membership for people who want the complete learning and community experience. Builder includes premium walkthroughs, structured learning tracks, capstones, private community access, live Builder Sessions, Office Hours, career-development resources, templates, reference implementations, and priority access to newly released content.",
        slug: "what-is-dsb-builder",
        links: [{ text: "View Builder membership", href: "/pricing" }],
      },
      {
        question: "What happens after I become a Builder?",
        answer:
          "After subscribing, you will be guided through the Builder Journey. You will connect your DSB account to Discord, receive the appropriate Builder access, learn how the platform is organized, join the community, complete the Prerequisites section, and then choose an engineering path. The experience is designed so that you do not have to figure everything out on your own.",
        slug: "what-happens-after-becoming-builder",
      },
      {
        question: "What is the Builder Journey?",
        answer:
          "The Builder Journey is a guided onboarding experience for new Builder members. It introduces the platform in five phases: Welcome to Builder, Join the Community, Build Your Foundation, Choose Your Engineering Path, and Build Momentum. Most members will work through the journey during their first 60 days, but you can move at the pace that works for you.",
        slug: "what-is-the-builder-journey",
      },
      {
        question: "What do Builder members receive each month?",
        answer:
          "Builder members receive ongoing access to the complete premium learning library, new and updated technical or career content as it is released, monthly community programming, private Builder discussions, and opportunities to learn directly with other members and practitioners. The exact monthly schedule is published in the private Builder Community Calendar inside Discord.",
        slug: "what-builders-receive-each-month",
      },
      {
        question: "What are Builder Sessions?",
        answer:
          "Builder Sessions are live, practical sessions where members learn by working through an engineering topic together. Sessions may include demonstrations, guided implementation, technical discussion, architecture decisions, troubleshooting, or collaborative building. Topics are selected to complement the curriculum and expose members to how practitioners approach real work.",
        slug: "what-are-builder-sessions",
      },
      {
        question: "What are Office Hours?",
        answer:
          "Office Hours give Builder members a dedicated place to ask questions, discuss projects, troubleshoot learning challenges, get feedback, and talk through career or technical decisions with the DSB team and community. They are intentionally conversational and shaped by what members need help with that month.",
        slug: "what-are-office-hours",
      },
      {
        question: "Are live sessions recorded?",
        answer:
          "Recording availability may vary by session. When a Builder Session or Office Hours call is recorded and approved for replay, the recording will be shared with Builder members. The event announcement will clarify whether a recording is planned or available.",
        slug: "are-live-sessions-recorded",
      },
      {
        question: "Can I try DSB before subscribing?",
        answer:
          "Yes. You can create a free account, explore selected resources, review the public curriculum, and join the broader DSB community before upgrading. Builder is available when you are ready for the full guided learning experience and private member programming.",
        slug: "can-i-try-before-subscribing",
        links: [
          { text: "Explore the curriculum", href: "/curriculum" },
          { text: "Compare memberships", href: "/pricing" },
        ],
      },
      {
        question: "Does DSB offer certificates?",
        answer:
          "DSB is developing a certification program built around demonstrated learning and practical work. Availability, requirements, and eligible learning paths will be announced through the platform and Builder community. Until then, members can still use completed projects, capstones, and documented implementations as evidence of their skills.",
        slug: "does-dsb-offer-certificates",
      },
    ],
  },
  {
    name: "Community",
    slug: "community",
    description: "Learn how Discord, live programming, collaboration, and community support fit into the DSB experience.",
    icon: "users",
    questions: [
      {
        question: "Is there a community for DSB members?",
        answer:
          "Yes. Community is a core part of The DevSec Blueprint. Our Discord brings together people at different stages of their careers to ask questions, share progress, discuss technical topics, find opportunities, and support one another. We want members to feel like they are learning with people—not simply logging into a platform alone.",
        slug: "is-there-a-community",
      },
      {
        question: "How do I join the DSB Discord?",
        answer:
          "Join through the official Discord invitation, then connect your Discord account to your registered DSB profile. Account connection is important because it allows the platform to assign the correct community access based on your membership. After your access is confirmed, review the rules and introduce yourself so the community can welcome you.",
        slug: "how-to-join-discord",
        links: [
          {
            text: "Join the DSB Discord",
            href: "https://discord.gg/devsecblueprint",
            external: true,
          },
        ],
      },
      {
        question: "Is Discord required?",
        answer:
          "You can use the learning platform without participating heavily in Discord, but connecting Discord is strongly recommended for Builder members. The private Builder community, monthly Community Calendar, event announcements, discussions, and several member opportunities are delivered through Discord. Without connecting your account, you may miss an important part of the Builder experience.",
        slug: "is-discord-required",
      },
      {
        question: "Where can I find the Builder Community Calendar?",
        answer:
          "The monthly Builder Community Calendar is published inside the private Builder area of the DSB Discord. It includes upcoming Office Hours, Builder Sessions, content releases, and other member programming. The calendar is a Builder benefit and is not published as a public website feature.",
        slug: "where-is-builder-community-calendar",
      },
      {
        question: "What kind of support can I receive from the community?",
        answer:
          "Members support one another through technical discussion, project feedback, career conversations, shared resources, opportunity discovery, and encouragement. DSB is not a guaranteed one-on-one coaching service, but we intentionally create spaces where members can ask thoughtful questions, learn from practitioners and peers, and avoid feeling isolated while they grow.",
        slug: "what-community-support",
      },
      {
        question: "Can I get help with a project in Discord?",
        answer:
          "Yes. Members can ask for help understanding requirements, debugging issues, reviewing architecture decisions, or working through blockers. We expect members to share enough context to help others understand the problem and to remain actively involved in solving it. The goal is collaborative learning—not having someone complete the project for you.",
        slug: "can-i-get-project-help-in-discord",
      },
      {
        question: "Can I participate if I cannot attend live events?",
        answer:
          "Yes. Live participation is valuable, but it is not required to remain a Builder. You can continue learning through the platform, engage asynchronously in Discord, and access session recordings when they are made available. The Community Calendar will help you plan around the events that matter most to you.",
        slug: "can-i-participate-without-live-events",
      },
      {
        question: "Is the community moderated?",
        answer:
          "Yes. DSB is actively moderated to protect a respectful, inclusive, and productive environment. Members are expected to follow the community guidelines, treat others with care, and contribute in ways that make the space better for everyone. Harassment, discrimination, exploitation, and repeated disruptive behavior are not tolerated.",
        slug: "is-community-moderated",
      },
    ],
  },
  {
    name: "Career Development",
    slug: "career-development",
    description: "See how DSB connects technical growth with career strategy, professional confidence, and opportunity.",
    icon: "briefcase",
    questions: [
      {
        question: "What Career Development resources are available?",
        answer:
          "DSB Career Development resources help members better understand the decisions, habits, and experiences that shape a technical career. Topics may include career planning, interviews, resumes, professional branding, compensation, promotions, workplace decisions, and lessons from real career experiences. The goal is to provide context that helps members make more informed decisions—not to promise a specific outcome.",
        slug: "what-career-development-resources",
      },
      {
        question: "What roles can DSB help me prepare for?",
        answer:
          "The curriculum supports skills used in roles such as DevSecOps Engineer, Cloud Security Engineer, Security Engineer, Platform Security Engineer, Security Automation Engineer, Cloud Engineer, and related infrastructure or application-security positions. Job titles vary by company, so we encourage members to focus on the underlying engineering capabilities rather than chasing a title alone.",
        slug: "what-roles-can-dsb-support",
      },
      {
        question: "Can DSB help me transition into Cloud Security or DevSecOps?",
        answer:
          "DSB can give you structure, practical projects, technical context, career resources, and a community to learn with during your transition. We cannot guarantee a job or replace the effort required to build experience, but we can help you understand what to learn, practice the work, and present your growth more clearly.",
        slug: "can-dsb-help-career-transition",
      },
      {
        question: "Does DSB provide job placement?",
        answer:
          "No. DSB does not guarantee employment or operate as a staffing agency. We support members by helping them build practical skills, complete portfolio-worthy work, access career-development resources, discover opportunities shared by the community, and learn from people with real industry experience.",
        slug: "does-dsb-provide-job-placement",
      },
      {
        question: "Does DSB provide resume or interview support?",
        answer:
          "Career topics may be covered through platform resources, Office Hours, community discussions, and special programming. Availability may vary, and Builder membership does not guarantee a private resume review, mock interview, or individualized career-coaching session. When these opportunities are offered, they will be announced to eligible members.",
        slug: "does-dsb-provide-resume-interview-support",
      },
      {
        question: "What certifications complement the DSB curriculum?",
        answer:
          "The best certification depends on your target role and current experience. Members commonly explore cloud, security, infrastructure, and Kubernetes certifications alongside practical project work. DSB encourages members to use certifications as one part of a broader development strategy that also includes hands-on experience, documented projects, and the ability to explain technical decisions.",
        slug: "what-certifications-complement-dsb",
      },
    ],
  },
  {
    name: "Billing",
    slug: "billing",
    description: "Review pricing, payments, cancellations, refunds, access changes, and account-management expectations.",
    icon: "credit-card",
    questions: [
      {
        question: "How much does Builder cost?",
        answer:
          "Current Builder pricing is listed on the official pricing page. Pricing may change as the platform evolves, but any applicable price and billing frequency will be shown before you complete your purchase.",
        slug: "how-much-does-builder-cost",
        links: [{ text: "View current pricing", href: "/pricing" }],
      },
      {
        question: "What payment methods are accepted?",
        answer:
          "DSB accepts supported credit and debit cards through Stripe. Available payment methods are shown during checkout.",
        slug: "what-payment-methods-accepted",
      },
      {
        question: "Can I cancel my Builder membership at any time?",
        answer:
          "Yes. You may cancel your Builder membership through your account settings. Cancellation prevents the next renewal, and your Builder access generally remains active through the end of the billing period you already paid for.",
        slug: "can-i-cancel-subscription",
      },
      {
        question: "What happens when my Builder membership ends?",
        answer:
          "When your paid access period ends, your account returns to the access level available to free members. Builder-only walkthroughs, learning resources, private Discord spaces, event access, and other premium benefits will no longer be available unless you renew. Your account and eligible learning history will remain subject to DSB's current platform and data-retention policies.",
        slug: "what-happens-when-builder-ends",
      },
      {
        question: "Does DSB offer refunds?",
        answer:
          "Builder purchases are non-refundable. Because digital content and member benefits become available immediately after purchase, members should review the pricing page, feature list, and applicable policies before subscribing. Please review the official Refund Policy for the complete terms.",
        slug: "does-dsb-offer-refunds",
        links: [{ text: "Review the Refund Policy", href: "/refund-policy" }],
      },
      {
        question: "Can I delete my account and data?",
        answer:
          "You may request account deletion through the available account controls or support process. Deletion may remove profile information and platform activity associated with your account, subject to legal, security, financial, and operational retention requirements described in DSB's policies.",
        slug: "can-i-delete-my-account",
        links: [{ text: "Review the Privacy Policy", href: "/privacy-policy" }],
      },
      {
        question: "What data does DSB collect?",
        answer:
          "DSB collects the information needed to operate the platform, manage accounts and memberships, track learning progress, support community access, process payments, improve the user experience, and protect the service. Please review the Privacy Policy for the current and complete description of how information is collected, used, and retained.",
        slug: "what-data-does-dsb-collect",
        links: [{ text: "Review the Privacy Policy", href: "/privacy-policy" }],
      },
    ],
  },
  {
    name: "Contributor Program",
    slug: "contributor-program",
    description: "Learn how meaningful contributors can support DSB content, projects, documentation, and community growth.",
    icon: "git-merge",
    questions: [
      {
        question: "How can I contribute to The DevSec Blueprint?",
        answer:
          "You can contribute through approved technical projects, walkthrough improvements, documentation, infrastructure code, security controls, bug fixes, content review, project maintenance, and other work that materially improves DSB. Contribution opportunities vary, and all contributions must follow the applicable repository guidance, DSB policies, and review process.",
        slug: "how-can-i-contribute",
        links: [
          {
            text: "Explore DSB on GitHub",
            href: "https://github.com/devsecblueprint",
            external: true,
          },
        ],
      },
      {
        question: "What qualifies as a meaningful contribution?",
        answer:
          "Meaningful contributions may include building or maintaining approved projects, materially improving documentation or walkthroughs, adding Terraform, CI/CD, policy, or security-control content, fixing broken labs, reviewing substantial technical content, or maintaining an approved project area. Small corrections are appreciated, but contributor benefits are based on sustained or material impact rather than the number of pull requests submitted.",
        slug: "what-is-a-meaningful-contribution",
      },
      {
        question: "Do contributors receive Builder access?",
        answer:
          "Eligible contributors may receive a DSB Builder grant. Contributor access is not lifetime access and is subject to the Contributor Policy, which is updated periodically. Renewal is reviewed based on continued meaningful contribution, maintenance, quality, and platform needs.",
        slug: "do-contributors-receive-builder-access",
      },
      {
        question: "Can I create content or teach through DSB?",
        answer:
          "Experienced practitioners may propose content, projects, walkthroughs, reviews, or community programming that align with DSB's mission and quality standards. Not every proposal will be accepted, and approved work may require additional review, licensing, editorial, or contributor agreements before publication.",
        slug: "can-i-create-content",
        links: [{ text: "Contact the DSB team", href: "/about/contact" }],
      },
      {
        question: "Does DSB use a Contributor License Agreement?",
        answer:
          "Yes. Approved contributors may be required to accept the DSB Contributor License Agreement before their work can be merged or published. The agreement helps clarify contribution rights and allows DSB to maintain, distribute, and protect the platform and its content responsibly.",
        slug: "does-dsb-use-a-cla",
      },
      {
        question: "Does DSB accept partnership or sponsorship inquiries?",
        answer:
          "Yes. DSB welcomes conversations with organizations and community leaders whose work aligns with our mission. Partnerships and sponsorships are evaluated based on member value, mission alignment, trust, and the ability to create meaningful opportunities for the community.",
        slug: "does-dsb-accept-partnerships",
        links: [
          { text: "Explore sponsorship opportunities", href: "/sponsorships" },
          { text: "Contact the DSB team", href: "/about/contact" },
        ],
      },
    ],
  },
  {
    name: "Technical",
    slug: "technical",
    description: "Review supported technologies, account requirements, cloud costs, devices, and technical support options.",
    icon: "terminal",
    questions: [
      {
        question: "Which cloud platforms and technologies does DSB cover?",
        answer:
          "DSB covers technologies used across modern DevSecOps and Cloud Security work, including AWS, Azure, Google Cloud, infrastructure as code, CI/CD, containers, Kubernetes, identity, policy as code, security automation, logging, detection, and related engineering practices. Coverage evolves as new learning paths and walkthroughs are released.",
        slug: "which-technologies-does-dsb-cover",
      },
      {
        question: "Do I need my own cloud account?",
        answer:
          "Many hands-on walkthroughs and projects require access to your own cloud account or development environment. Each activity should identify its requirements before you begin. Members are responsible for securing their accounts, following provider terms, and removing resources when they are no longer needed.",
        slug: "do-i-need-my-own-cloud-account",
      },
      {
        question: "Do I need to pay for cloud services?",
        answer:
          "Some activities may fit within cloud-provider free tiers or low-cost usage, but free-tier eligibility is not guaranteed and provider pricing can change. DSB will identify known cost considerations when practical, but members are responsible for monitoring their own usage, budgets, and charges. Always review the project requirements before deploying resources.",
        slug: "do-i-need-to-pay-for-cloud",
      },
      {
        question: "What tools do I need to complete DSB projects?",
        answer:
          "Requirements vary by project, but members should expect to use source control, a code editor, command-line tools, scripting, containers, infrastructure-as-code tooling, and one or more cloud platforms. Each walkthrough or capstone should list the required tools, accounts, permissions, and setup steps before the implementation begins.",
        slug: "what-tools-do-i-need",
      },
      {
        question: "What operating systems are supported?",
        answer:
          "The DSB platform works in modern web browsers. Hands-on projects may be completed from Linux, macOS, or Windows depending on the required tools. Windows users may need Windows Subsystem for Linux, containers, or another compatible development environment for certain projects.",
        slug: "what-operating-systems-supported",
      },
      {
        question: "How do I report a platform bug or technical issue?",
        answer:
          "Report platform bugs through the approved GitHub issue tracker or the designated DSB support channel. Include the page or feature affected, steps to reproduce the issue, the expected and actual behavior, relevant screenshots or error messages, and details about your browser or environment. Please do not post credentials, secrets, payment information, or other sensitive data.",
        slug: "how-to-report-a-bug",
        links: [
          {
            text: "Report an issue on GitHub",
            href: "https://github.com/devsecblueprint/devsecblueprint/issues",
            external: true,
          },
          { text: "Contact support", href: "/about/contact" },
        ],
      },
    ],
  },
];
