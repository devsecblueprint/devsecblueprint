export interface PlanFeature {
  text: string;
  included: boolean;
}

export interface PlanContent {
  tier: string;
  name: string;
  tagline: string;
  description: string;
  billingNote?: string;
  features: PlanFeature[];
  notIncluded?: PlanFeature[];
  supportBoundary?: {
    title: string;
    description: string;
    restrictionsLabel?: string;
    restrictions: string[];
  };
  disclaimer?: string;
  comingSoon?: boolean;
}

export const PLANS: PlanContent[] = [
  {
    tier: "FREE",
    name: "Free",
    tagline: "Discover the projects. Understand the landscape.",
    description: "The free experience preserves DSB's open-source identity, allows people to discover the projects, and gives contributors a path to participate. Free users can understand what a project is, why it matters, and what it demonstrates — without the full guided learning experience.",
    features: [
      { text: "Public DSB project pages", included: true },
      { text: "Project purpose and problem statements", included: true },
      { text: "Architecture diagrams", included: true },
      { text: "Tool lists and prerequisites", included: true },
      { text: "Learning objectives and skills demonstrated", included: true },
      { text: "High-level implementation flows", included: true },
      { text: "Screenshots and expected outcomes", included: true },
      { text: "Public learning roadmaps", included: true },
      { text: "Public blog posts and updates", included: true },
      { text: "Open-source code and GitHub repositories", included: true },
      { text: "Terraform, CI/CD examples, policies, and sample applications", included: true },
      { text: "Basic README documentation", included: true },
      { text: "Contribution guidance", included: true },
      { text: "Discord access", included: false },
      { text: "GitHub Issues for bugs, broken labs, security concerns, and documentation corrections", included: true },
    ],
    notIncluded: [
      { text: "Full written walkthroughs", included: false },
      { text: "Step-by-step deployment instructions", included: false },
      { text: "Troubleshooting playbooks", included: false },
      { text: "Premium templates or checklists", included: false },
      { text: "Office hours", included: false },
      { text: "Builder tracks", included: false },
      { text: "Capstone review", included: false },
      { text: "Certificates of completion", included: false },
      { text: "Certification giveaway eligibility", included: false },
    ],
  },
  {
    tier: "EXPLORER",
    name: "Explorer",
    tagline: "The self-paced implementation tier for builders.",
    description: "DSB Explorer is the self-paced implementation tier for builders who want the full learning experience without a high-touch cohort commitment.",
    billingNote: "Billed annually.",
    features: [
      { text: "Everything in Free", included: true },
      { text: "Access to every full expert-written walkthrough", included: true },
      { text: "Step-by-step project implementation guidance", included: true },
      { text: "Deployment and configuration instructions", included: true },
      { text: "Infrastructure and pipeline breakdowns", included: true },
      { text: "Security architecture explanations", included: true },
      { text: "Troubleshooting playbooks", included: true },
      { text: "Common errors and fixes", included: true },
      { text: "Validation checklists", included: true },
      { text: "Premium templates and checklists", included: true },
      { text: "Premium resource library", included: true },
      { text: "Premium Discord access and member-only channels", included: true },
      { text: "Eligibility for quarterly certification giveaways", included: true },
      { text: "Early access to new Premium walkthroughs and resources", included: true },
    ],
    notIncluded: [
      { text: "One-on-one support", included: false },
      { text: "Private troubleshooting", included: false },
      { text: "Individual code review", included: false },
      { text: "Personal project review", included: false },
      { text: "Office hours", included: false },
      { text: "Capstone review", included: false },
      { text: "Certificate of completion", included: false },
      { text: "Resume reviews", included: false },
      { text: "Career coaching", included: false },
      { text: "Mock interviews", included: false },
      { text: "Consulting or advisory services", included: false },
    ],
    supportBoundary: {
      title: "Explorer Support Boundary",
      description: "Explorer support is asynchronous and community-based. Members may ask questions in designated Discord channels, but DSB does not guarantee response times, issue resolution, or individualized debugging.",
      restrictionsLabel: "Premium members may not expect the founder to:",
      restrictions: [
        "Review their entire environment",
        "Debug large logs or repositories privately",
        "Build missing portions of their project",
        "Respond to direct messages",
        "Provide private consulting through Discord",
      ],
    },
    disclaimer: "All Explorer subscriptions are non-refundable.",
  },
  {
    tier: "BUILDER",
    name: "Builder",
    tagline: "Structured paths. Group accountability. More support.",
    description: "DSB Builder is for members who want a defined path, group accountability, and more structure than self-paced access alone.",
    billingNote: "Billed annually.",
    features: [
      { text: "Everything in Explorer", included: true },
      { text: "Structured learning tracks", included: true },
      { text: "Recommended walkthrough and project sequence", included: true },
      { text: "Builder-only Discord channels", included: true },
      { text: "Monthly group office hours", included: true },
      { text: "Group learning sessions", included: true },
      { text: "Certification study guidance", included: true },
      { text: "Project milestone checklists", included: true },
      { text: "Group feedback sessions", included: true },
      { text: "Builder badge or recognition", included: true },
      { text: "Priority access to new DSB content", included: true },
    ],
    notIncluded: [
      { text: "One-on-one calls", included: false },
      { text: "Individual mentorship", included: false },
      { text: "Private code review", included: false },
      { text: "Personal career services", included: false },
      { text: "Capstone review", included: false },
      { text: "Certificate of completion", included: false },
      { text: "Unlimited troubleshooting", included: false },
      { text: "Guaranteed completion of any project or certification", included: false },
    ],
    supportBoundary: {
      title: "Builder Office Hour Rules",
      description: "Office hours are group-based, scoped, and time-limited. Builder does not become private consulting because a member pays more.",
      restrictionsLabel: "Members are expected to:",
      restrictions: [
        "Arrive with focused questions",
        "Share concise context",
        "Use walkthroughs and documentation before asking",
        "Respect session time limits",
        "Understand not every question can be addressed live",
        "Participate in good faith",
      ],
    },
    disclaimer: "All Builder subscriptions are non-refundable.",
  },
  {
    tier: "BUILDER_ACADEMY",
    name: "Builder Academy",
    tagline: "The complete DevSecOps career accelerator.",
    description: "The full DSB experience. Everything in Builder plus live office hours, certificates of completion, and certification giveaway eligibility. The ultimate investment in your DevSecOps career.",
    billingNote: "Billed annually.",
    comingSoon: true,
    features: [
      { text: "Everything in Builder", included: true },
      { text: "Live office hours", included: true },
      { text: "Certificates of completion", included: true },
      { text: "Certification giveaway eligibility", included: true },
      { text: "Academy Discord role and channels", included: true },
      { text: "Direct access to Damien", included: true },
    ],
    disclaimer: "All Builder Academy subscriptions are non-refundable.",
  },
];
