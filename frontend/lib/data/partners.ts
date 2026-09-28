/**
 * Partners Data File
 *
 * Typed partner data for the Sponsorships page Partners section.
 * If the PARTNERS array is empty, the Partners section will not render.
 */

export interface Partner {
  /** Partner display name */
  name: string;
  /** Path to partner logo asset (relative to public directory) */
  logoPath: string;
  /** Optional URL to partner website */
  url?: string;
}

/**
 * Organization we connect with, but not a sponsor or community partner.
 * A logo is optional; when omitted, a clean text treatment is rendered.
 */
export interface Organization {
  /** Organization display name */
  name: string;
  /** URL to the organization's official website */
  url: string;
  /** Optional path to an approved logo asset (relative to public directory) */
  logoPath?: string;
}

export const PARTNERS: Partner[] = [
  {
    name: "GRC Engineering Club",
    logoPath: "/partners/grc_eng_club_logo.svg",
    url: "https://grcengclub.com",  // ← this makes the logo clickable
  },
  {
    name: "All Things STEM With Ashley",
    logoPath: "/partners/all_things_stem_with_ashley_logo.svg",
    url: "https://www.linkedin.com/company/all-things-stem-with-ashley"
  },
  {
    name: "Techtual Consulting",
    logoPath: "/partners/techtual_consulting.svg",
    url: "https://techtualconsulting.tech/"
  },
  {
    name: "Black IT Academy",
    logoPath: "/partners/black_it_academy.webp",
    url: "https://blackitacademy.org/"
  },
  {
    name: "Techpreneurship Academy",
    logoPath: "/partners/ta.svg",
    url: "https://tac2cblueprint.com/"
  }
];

/**
 * Organizations whose tools and expertise are relevant to what the DSB
 * community is learning and building. Listing here does not imply sponsorship,
 * product endorsement, or involvement in creating or approving DSB content.
 * If the ORGANIZATIONS_WE_WORK_WITH array is empty, the group will not render.
 */
export const ORGANIZATIONS_WE_WORK_WITH: Organization[] = [
  {
    name: "Authentik",
    url: "https://goauthentik.io/",
    // Official Authentik brand mark, sourced from goauthentik.io.
    logoPath: "/partners/authentik.svg",
  },
];
