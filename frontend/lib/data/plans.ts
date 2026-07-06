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

export const BUILDER_PLAN: PlanContent = {
  tier: "BUILDER",
  name: "Builder",
  tagline: "Structured paths. Group accountability. Real support.",
  description:
    "DSB Builder gives you the full learning experience: expert walkthroughs, structured tracks, group office hours, and a community of builders shipping real DevSecOps projects.",
  billingNote: "Billed monthly. Cancel anytime.",
  features: [
    { text: "Full expert-written walkthroughs", included: true },
    { text: "Step-by-step project implementation guidance", included: true },
    { text: "Structured learning tracks", included: true },
    { text: "Monthly group office hours", included: true },
    { text: "Builder-only Discord channels", included: true },
    { text: "Premium templates and checklists", included: true },
    { text: "Troubleshooting playbooks", included: true },
    { text: "Certification study guidance", included: true },
    { text: "Project milestone checklists", included: true },
    { text: "Group feedback sessions", included: true },
    { text: "Priority access to new content", included: true },
    { text: "Quarterly certification giveaway eligibility", included: true },
  ],
  disclaimer: "All Builder subscriptions are non-refundable.",
};

export const SUBSCRIPTION_COMPARISONS: ComparisonItem[] = [
  {
    name: "DSB Builder",
    description: "Hands-on DevSecOps projects, guided walkthroughs, and group support",
    price: "$29/mo",
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
