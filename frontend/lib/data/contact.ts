export type InquiryType =
  | "membership-support"
  | "technical-support"
  | "contributions"
  | "partnerships"
  | "speaking-media"
  | "general-inquiry";

export interface InquiryCategory {
  type: InquiryType;
  label: string;
  description: string; // max 120 chars
  icon: string;
  responseTime: string;
}

export interface ContactFormData {
  fullName: string; // 1–100 chars
  email: string; // 1–254 chars, standard email pattern
  organization: string; // 0–100 chars (optional)
  inquiryType: InquiryType;
  subject: string; // 1–150 chars
  message: string; // 10–2000 chars
}

export interface ContactSubmission {
  submit(
    data: ContactFormData
  ): Promise<{ success: boolean; error?: string }>;
}

export const INQUIRY_CATEGORIES: InquiryCategory[] = [
  {
    type: "membership-support",
    label: "Membership & Community",
    description:
      "Questions about Builder membership, curriculum, onboarding, community access, or getting started.",
    icon: "users",
    responseTime: "1 business day",
  },
  {
    type: "technical-support",
    label: "Technical Support",
    description:
      "Report issues with platform features, content loading, authentication, or lab environments.",
    icon: "wrench",
    responseTime: "2 business days",
  },
  {
    type: "contributions",
    label: "Contributions",
    description:
      "Interested in contributing content, code, or educational resources to the DSB platform.",
    icon: "git-pull-request",
    responseTime: "3 business days",
  },
  {
    type: "partnerships",
    label: "Partnerships",
    description:
      "Explore business collaborations, sponsorships, or integration opportunities with DSB.",
    icon: "handshake",
    responseTime: "3 business days",
  },
  {
    type: "speaking-media",
    label: "Speaking/Media",
    description:
      "Reach out about speaking engagements, podcast appearances, or press inquiries.",
    icon: "microphone",
    responseTime: "5 business days",
  },
  {
    type: "general-inquiry",
    label: "General Inquiry",
    description:
      "Any other questions or feedback not covered by the categories above.",
    icon: "message-circle",
    responseTime: "3 business days",
  },
];

/**
 * Contact email routing.
 * community@ handles membership, curriculum, onboarding, and community questions.
 * info@ handles general company inquiries.
 * Specialized addresses (technical support, partnerships, media) route through the contact form.
 */
export const CONTACT_EMAILS = {
  community: 'community@devsecblueprint.com',
  general: 'info@devsecblueprint.com',
} as const;

export const INQUIRY_HELPER_TEXT: Record<InquiryType, string> = {
  "membership-support":
    "Questions about billing, plan changes, or account access.",
  "technical-support":
    "Issues with platform features, content loading, or authentication.",
  contributions:
    "Interested in contributing content, code, or resources to DSB.",
  partnerships:
    "Business collaborations, sponsorships, or integration opportunities.",
  "speaking-media":
    "Speaking engagements, podcast appearances, or press inquiries.",
  "general-inquiry":
    "Anything else not covered by the categories above.",
};
