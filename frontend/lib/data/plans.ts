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

export interface ComparisonItem {
  name: string;
  description: string;
  price: string;
  priceNote?: string;
}

export const FREE_PLAN: PlanContent = {
  tier: "FREE",
  name: "Free",
  tagline: "Start learning DevSecOps at your own pace.",
  description:
    "Access core learning modules, quizzes, and a thriving Discord community with curated news feeds, career resources, and peer support — all completely free.",
  features: [
    { text: "Core learning modules and lessons", included: true },
    { text: "Knowledge-check quizzes", included: true },
    { text: "Progress tracking and streaks", included: true },
    { text: "Badge and achievement system", included: true },
    { text: "Community Discord access (general, introductions, suggestions, wins)", included: true },
    { text: "DSB Contributors channel", included: true },
    { text: "Daily tech news feed", included: true },
    { text: "Security news feed", included: true },
    { text: "Investment news feed", included: true },
    { text: "Content corner (articles and resources)", included: true },
    { text: "Job board channel", included: true },
    { text: "Hangout channel (gaming and general discussion)", included: true },
  ],
};

export const BUILDER_PLAN: PlanContent = {
  tier: "BUILDER",
  name: "Builder",
  tagline: "Structured paths. Group accountability. Real support.",
  description:
    "DSB Builder gives you the full learning experience: expert walkthroughs, structured tracks, group office hours, and a community of builders shipping real DevSecOps projects.",
  billingNote: "Billed monthly. Cancel anytime.",
  features: [
    { text: "Everything in Free", included: true },
    { text: "Full expert-written walkthroughs", included: true },
    { text: "Step-by-step project implementation guidance", included: true },
    { text: "Capstone project submissions and reviews", included: true },
    { text: "Structured learning tracks", included: true },
    { text: "Monthly group office hours (Google Meet)", included: true },
    { text: "Private builder discussion channel (walkthroughs, projects, technical collaboration)", included: true },
    { text: "Mini-capstone library (catalog of guided projects)", included: true },
    { text: "Reference implementations and architecture breakdowns", included: true },
    { text: "Career development forum (resume, LinkedIn, interview prep, salary)", included: true },
    { text: "Job referrals channel (community hiring and networking)", included: true },
    { text: "Builder announcements and content releases", included: true },
    { text: "Builder handbook, rules, and documentation", included: true },
    { text: "Premium templates and checklists", included: true },
    { text: "Troubleshooting playbooks", included: true },
    { text: "Priority access to new content", included: true },
    { text: "Eligibility for Builder-exclusive community giveaways (subject to availability)", included: true },],
  disclaimer: "All Builder subscriptions are non-refundable.",
};

export const SUBSCRIPTION_COMPARISONS: ComparisonItem[] = [
  {
    name: "DSB Builder",
    description: "Hands-on DevSecOps projects, guided walkthroughs, and group support",
    price: "$29.99/mo",
    priceNote: "Cancel anytime",
  },
  {
    name: "TCM Security",
    description: "Cybersecurity video courses and labs",
    price: "$30/mo",
    priceNote: "All-Access membership",
  },
  {
    name: "LinkedIn Learning",
    description: "Professional development video courses",
    price: "$39.99/mo",
    priceNote: "Individual plan",
  },
  {
    name: "Pluralsight Complete",
    description: "Video courses and hands-on labs",
    price: "$39/mo",
    priceNote: "Billed annually",
  },
  {
    name: "Hack The Box Academy",
    description: "Offensive security labs and cert prep",
    price: "$41/mo",
    priceNote: "Billed annually",
  },
  {
    name: "INE Premium",
    description: "Cybersecurity and networking training",
    price: "$62/mo",
    priceNote: "Billed annually",
  },
];

// Keep PLANS export for backward compatibility with tests
export const PLANS: PlanContent[] = [BUILDER_PLAN];
