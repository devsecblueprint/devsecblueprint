/**
 * Companies Data File
 *
 * Company logos displayed in the "Companies Where DSB Members Have Landed" carousel.
 * Add new entries here to include more company logos in the marquee.
 */

export interface Company {
  /** Company display name (used for alt text and as a text fallback) */
  name: string;
  /**
   * Optional URL to company logo (local asset under /public/companies).
   * When omitted, the carousel renders a clean text treatment of `name`.
   */
  logoUrl?: string;
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
  {
    name: "Invesco",
    logoUrl: "/companies/invesco.svg",
    url: "https://www.invesco.com/corporate/en/home.html"
  },
  {
    name: "IBM",
    logoUrl: "/companies/ibm.png",
    url: "https://www.ibm.com",
  },
  // {
  //   name: "T-Mobile",
  //   logoUrl: "/companies/t-mobile.svg",
  //   url: "https://www.t-mobile.com",
  // },
];
