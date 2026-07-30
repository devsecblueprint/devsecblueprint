/**
 * Sponsorship Data File
 *
 * Structured data for the Sponsorships page including community metrics,
 * audience segments, sponsorship opportunities, benefits, principles, and FAQ.
 */

export type SponsorshipOpportunityType =
  | "founding"
  | "curriculum"
  | "walkthrough"
  | "builder-scholarship"
  | "workshop"
  | "community"
  | "platform"
  | "talent-hiring";

export type BudgetRange =
  | "under-1000"
  | "1000-2500"
  | "2500-5000"
  | "5000-10000"
  | "10000-25000"
  | "25000-plus";

export interface MetricCard {
  value: string;
  label: string;
}

export interface AudienceCard {
  title: string;
  description: string;
}

export interface OpportunityCard {
  title: string;
  type: SponsorshipOpportunityType;
  benefits: string[];
}

export interface BenefitCard {
  title: string;
  description: string;
}

export interface PrincipleCard {
  title: string;
  description: string;
}

export interface SponsorshipFAQItem {
  id: string;
  question: string;
  answer: string;
}

export const COMMUNITY_METRICS: MetricCard[] = [
  { value: "1,000+", label: "LinkedIn Followers" },
  { value: "800+", label: "Registered Platform Users" },
  { value: "140+", label: "Countries Represented" },
  { value: "10,000+", label: "Organic Impressions" },
  { value: "7,000+", label: "Unique Organic Impressions" },
  { value: "400+", label: "Clicks and Social Engagements" },
];

export const AUDIENCE_SEGMENTS: AudienceCard[] = [
  {
    title: "DevSecOps Engineers",
    description:
      "Professionals integrating security into CI/CD pipelines and automating compliance across cloud-native infrastructure.",
  },
  {
    title: "Cloud Security Practitioners",
    description:
      "Engineers focused on securing cloud workloads, managing identity and access, and implementing defense-in-depth strategies.",
  },
  {
    title: "Security Engineers",
    description:
      "Specialists building security tooling, performing threat modeling, and implementing application security controls.",
  },
  {
    title: "Developers and Platform Engineers",
    description:
      "Software engineers and platform teams adopting shift-left security practices and building secure delivery pipelines.",
  },
  {
    title: "Emerging Technical Talent",
    description:
      "Early-career engineers and career changers actively building hands-on skills in DevSecOps and cloud security.",
  },
  {
    title: "Technical Leaders and Hiring Teams",
    description:
      "Engineering managers and recruiters seeking security-focused talent with demonstrated practical skills.",
  },
];

export const SPONSORSHIP_OPPORTUNITIES: OpportunityCard[] = [
  {
    title: "Founding Sponsorships",
    type: "founding",
    benefits: [
      "Permanent recognition as a founding partner across the platform",
      "Logo placement on the homepage and sponsorships page",
      "Co-branded content opportunities with the DSB team",
      "Priority access to new sponsorship features and formats",
      "Direct input on community initiatives and roadmap",
    ],
  },
  {
    title: "Curriculum and Walkthrough Sponsorships",
    type: "curriculum",
    benefits: [
      "Sponsor specific learning modules or walkthrough projects",
      "Brand visibility within the learning path experience",
      "Attribution in course materials and completion certificates",
      "Access to anonymized learner engagement metrics",
    ],
  },
  {
    title: "Builder Scholarship Sponsorships",
    type: "builder-scholarship",
    benefits: [
      "Fund scholarships for underrepresented learners in security engineering",
      "Brand recognition in scholarship announcements and recipient communications",
      "Annual impact report on scholarship outcomes",
      "Community recognition as a workforce development supporter",
    ],
  },
  {
    title: "Technical Workshops and Live Sessions",
    type: "workshop",
    benefits: [
      "Sponsor live technical workshops or hands-on lab sessions",
      "Present your tools or solutions in an educational context",
      "Engage directly with an active, technical audience",
      "Post-session brand visibility in recorded content",
      "Co-develop workshop curriculum with the DSB team",
    ],
  },
  {
    title: "Community and Platform Sponsorships",
    type: "community",
    benefits: [
      "Support Discord community operations and moderation",
      "Sponsor community events, challenges, or hackathons",
      "Brand presence in community channels and communications",
      "Opportunity to host dedicated community office hours",
    ],
  },
  {
    title: "Talent and Hiring Partnerships",
    type: "talent-hiring",
    benefits: [
      "Access to a pipeline of skilled DevSecOps practitioners",
      "Post job opportunities to the DSB community",
      "Branded presence in career development resources",
      "Priority placement in job board and hiring channels",
      "Participation in portfolio review and mentorship events",
      "Anonymized talent pool analytics and engagement metrics",
    ],
  },
];

export const WHY_PARTNER_BENEFITS: BenefitCard[] = [
  {
    title: "A Focused Technical Audience",
    description:
      "Reach engineers actively learning and implementing DevSecOps, cloud security, and secure software delivery. Our community is composed of practitioners, not passive browsers.",
  },
  {
    title: "Learning Through Real Systems",
    description:
      "DSB teaches through hands-on projects and real infrastructure, not slide decks. Sponsors are associated with practical skill-building that engineers value and remember.",
  },
  {
    title: "Community Trust",
    description:
      "Our editorial principles ensure sponsorships maintain credibility. We only partner with organizations whose tools and services genuinely serve our community's learning goals.",
  },
  {
    title: "Meaningful Community Impact",
    description:
      "Your sponsorship directly funds scholarships, platform development, and educational content that makes security engineering accessible to a global audience.",
  },
];

export const SPONSORSHIP_PRINCIPLES: PrincipleCard[] = [
  {
    title: "Technical Independence",
    description:
      "Sponsorship does not influence technical recommendations, tool selections, or curriculum content. Our educational guidance remains objective and learner-focused.",
  },
  {
    title: "Clear Disclosure",
    description:
      "All sponsored content, partnerships, and brand placements are clearly labeled. Our community always knows when content involves a sponsor relationship.",
  },
  {
    title: "Educational Value",
    description:
      "Sponsored integrations must provide genuine educational value to learners. We do not accept sponsorships that serve only promotional purposes without learning outcomes.",
  },
  {
    title: "Audience Relevance",
    description:
      "We only partner with organizations whose products, services, or mission are directly relevant to DevSecOps and cloud security practitioners.",
  },
  {
    title: "Editorial Control",
    description:
      "The DSB team retains full editorial control over all content, including sponsored materials. Sponsors may suggest topics but cannot dictate conclusions or recommendations.",
  },
  {
    title: "Limited Sponsorship Inventory",
    description:
      "We intentionally limit the number of active sponsorships to maintain quality, prevent ad fatigue, and ensure each partner receives meaningful visibility and engagement.",
  },
];

export const SPONSORSHIP_FAQ: SponsorshipFAQItem[] = [
  {
    id: "what-is-dsb-sponsorship",
    question: "What does it mean to sponsor The DevSec Blueprint?",
    answer:
      "Sponsoring DSB means supporting the development of free and accessible DevSecOps education while gaining visibility with a focused technical audience. Sponsorships fund scholarships, platform development, and content creation.",
  },
  {
    id: "how-are-sponsorships-structured",
    question: "How are sponsorship packages structured?",
    answer:
      "Each sponsorship is custom-developed around your organizational goals. We discuss your objectives, audience alignment, and budget to create a package that delivers meaningful value for both your team and our community.",
  },
  {
    id: "what-is-the-minimum-commitment",
    question: "What is the minimum sponsorship commitment?",
    answer:
      "Sponsorship packages start at various levels depending on the opportunity type. We work with organizations of all sizes and can structure partnerships to fit a range of budgets. Reach out through the inquiry form to discuss options.",
  },
  {
    id: "does-sponsorship-guarantee-endorsement",
    question: "Does sponsorship guarantee a product endorsement?",
    answer:
      "No. Sponsorship does not guarantee endorsement, positive reviews, or recommendations. DSB maintains full editorial independence. We only recommend tools and services based on genuine technical merit and educational value.",
  },
  {
    id: "how-do-i-measure-sponsorship-impact",
    question: "How do I measure the impact of my sponsorship?",
    answer:
      "We provide sponsors with regular reports including engagement metrics, community reach, and content performance data. Specific metrics depend on your sponsorship type and are agreed upon during package development.",
  },
  {
    id: "can-i-sponsor-specific-content",
    question: "Can I sponsor a specific course or walkthrough?",
    answer:
      "Yes. Curriculum and walkthrough sponsorships allow you to support specific learning modules. Your brand receives attribution within the learning experience while the DSB team retains editorial control over all content.",
  },
  {
    id: "what-is-the-sponsorship-process",
    question: "What is the process to become a sponsor?",
    answer:
      "Submit an inquiry through the form below with your goals and budget range. Our team will review your submission and schedule a conversation to explore alignment and develop a custom sponsorship package.",
  },
];

export const BUDGET_OPTIONS: { value: BudgetRange; label: string }[] = [
  { value: "under-1000", label: "Under $1,000" },
  { value: "1000-2500", label: "$1,000 - $2,500" },
  { value: "2500-5000", label: "$2,500 - $5,000" },
  { value: "5000-10000", label: "$5,000 - $10,000" },
  { value: "10000-25000", label: "$10,000 - $25,000" },
  { value: "25000-plus", label: "$25,000+" },
];

export const OPPORTUNITY_OPTIONS: {
  value: SponsorshipOpportunityType;
  label: string;
}[] = [
  { value: "founding", label: "Founding Sponsorship" },
  { value: "curriculum", label: "Curriculum Sponsorship" },
  { value: "walkthrough", label: "Walkthrough Sponsorship" },
  { value: "builder-scholarship", label: "Builder Scholarship Sponsorship" },
  { value: "workshop", label: "Workshop Sponsorship" },
  { value: "community", label: "Community Sponsorship" },
  { value: "platform", label: "Platform Sponsorship" },
  { value: "talent-hiring", label: "Talent/Hiring Partnership" },
];
