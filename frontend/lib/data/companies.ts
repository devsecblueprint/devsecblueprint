/**
 * Companies Data File
 *
 * Company logos displayed in the "Companies Where DSB Members Have Landed" carousel.
 * Add new entries here to include more company logos in the marquee.
 */

export interface Company {
  /** Company display name (used for alt text) */
  name: string;
  /** URL to company logo (Brandfetch CDN or local asset) */
  logoUrl: string;
  /** Optional link to company website */
  url?: string;
}

export const COMPANIES: Company[] = [
  {
    name: "Infosys",
    logoUrl: "/companies/infosys.svg",
    url: "https://www.infosys.com",
  },
  {
    name: "Citi",
    logoUrl: "/companies/citi.svg",
    url: "https://www.citigroup.com",
  },
  // {
  //   name: "T-Mobile",
  //   logoUrl: "/companies/t-mobile.svg",
  //   url: "https://www.t-mobile.com",
  // },
];
