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
