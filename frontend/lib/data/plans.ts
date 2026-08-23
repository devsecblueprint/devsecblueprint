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

export const FREE_PLAN: PlanContent = {
  tier: "FREE",
  name: "Free",
  tagline: "Not ready for Builder? Start free.",
  description:
    "Get started with foundational DevSecOps and Cloud Security content, track your learning progress, and join the broader DSB community — at no cost.",
  features: [
    { text: "Access foundational learning content", included: true },
    { text: "Track learning progress and achievements", included: true },
    { text: "Join the broader DSB community", included: true },
  ],
};

export const BUILDER_PLAN: PlanContent = {
  tier: "BUILDER",
  name: "Builder",
  tagline: "The full DSB learning experience.",
  description:
    "DSB Builder gives you structured curriculum, real engineering projects, technical feedback, and community support — everything you need to build practical DevSecOps and Cloud Security skills.",
  billingNote: "Billed monthly. Cancel anytime.",
  features: [
    { text: "Expert-written technical walkthroughs", included: true },
    { text: "Structured learning tracks", included: true },
    { text: "Guided projects and mini-capstones", included: true },
    { text: "Eligible project and capstone reviews", included: true },
    { text: "Technical feedback", included: true },
    { text: "Private Builder community access", included: true },
    { text: "Builder Sessions", included: true },
    { text: "Group Office Hours", included: true },
    { text: "Premium templates and reference implementations", included: true },
    { text: "Career development resources", included: true },
    { text: "Priority access to new DSB content and programming", included: true },
  ],
  disclaimer: "All Builder subscriptions are non-refundable.",
};

// Keep PLANS export for backward compatibility with tests
export const PLANS: PlanContent[] = [BUILDER_PLAN];
