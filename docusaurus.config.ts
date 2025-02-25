import { themes as prismThemes } from "prism-react-renderer";
import type { Config } from "@docusaurus/types";
import type * as Preset from "@docusaurus/preset-classic";

require("dotenv").config();

const config: Config = {
  title: "DSB",
  tagline: "DevSec Blueprint",
  favicon: "img/logo.svg",

  // Set the production url of your site here
  url: "https://devsecblueprint.com",
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: "/",

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: "devsecblueprint", // Usually your GitHub org/user name.
  projectName: "devsecblueprint", // Usually your repo name.

  onBrokenLinks: "throw",
  onBrokenMarkdownLinks: "warn",

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: "en", // Default language of your site
    locales: [
      "en", // English
      "es", // Spanish
      "fr", // French
      "de", // German
      "it", // Italian
      "zh-CN", // Chinese (Simplified)
      "zh-TW", // Chinese (Traditional)
      "ja", // Japanese
      "pt-BR", // Portuguese (Brazil)
      "pt-PT", // Portuguese (Portugal)
      "ar", // Arabic
      "hi", // Hindi
      "vi", // Vietnamese
    ],
  },

  plugins: [
    require.resolve("docusaurus-plugin-image-zoom"),
    require.resolve("docusaurus-lunr-search"),
  ],

  presets: [
    [
      "classic",
      {
        docs: {
          sidebarPath: "./sidebars.ts",
          routeBasePath: "/",
          path: "docs",
        },
        blog: false,
        theme: {
          customCss: "./src/css/custom.css",
        },
        gtag: {
          trackingID: process.env.GOOGLE_ANALYTICS_ID,
          anonymizeIP: false,
        },
        googleTagManager: {
          containerId: process.env.GOOGLE_TAG_MANAGER_ID,
        },
        sitemap: {
          lastmod: "date",
          changefreq: "weekly",
          priority: 0.5,
          ignorePatterns: ["/tags/**"],
          filename: "sitemap.xml",
          createSitemapItems: async (params) => {
            const { defaultCreateSitemapItems, ...rest } = params;
            const items = await defaultCreateSitemapItems(rest);
            return items.filter((item) => !item.url.includes("/page/"));
          },
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    // Replace with your project's social card
    image: "img/logo.jpg",
    navbar: {
      logo: {
        className: "dsb-logo",
        alt: "DSB Logo",
        src: "img/logo.svg",
      },
      items: [
        {
          type: "docSidebar",
          sidebarId: "tutorialSidebar",
          position: "left",
          label: "The DevSec Blueprint",
        },
        {
          href: "https://discord.gg/enMmUNq8jc",
          label: "Discord",
          position: "right",
        },
        {
          type: "localeDropdown",
          position: "right",
        },
        {
          href: "https://github.com/devsecblueprint/devsecblueprint",
          position: "right",
          className: "header-github-link",
          "aria-label": "GitHub Repository",
        },
      ],
    },
    announcementBar: {
      id: "announcement", // Any unique ID
      content:
        "🌟 If you like what you see, give the DSB a STAR and share with friends! 🌟",
      backgroundColor: "#000000", // Defaults to `#fff`
      textColor: "#ffbe00", // Defaults to `#000`
      isCloseable: false, // Defaults to `true`
    },
    footer: {
      style: "dark",
      links: [
        {
          title: "Socials",
          items: [
            {
              label: "Discord",
              href: "https://discord.gg/enMmUNq8jc",
            },
            {
              label: "LinkedIn",
              href: "https://www.linkedin.com/company/devsecblueprint/",
            },
            {
              label: "Twitter (X)",
              href: "https://x.com/@devsecblueprint",
            },
          ],
        },
        {
          title: "Blueprint Help",
          items: [
            {
              label: "Report Issue",
              href: "https://github.com/devsecblueprint/devsecblueprint/issues",
            },
            {
              label: "GitHub Repository",
              href: "https://github.com/devsecblueprint/devsecblueprint",
            },
          ],
        },
        {
          title: "Community",
          items: [
            {
              label: "Code Of Conduct",
              href: "https://github.com/devsecblueprint/devsecblueprint/blob/main/CODE_OF_CONDUCT.md/",
            },
            {
              label: "License",
              href: "https://github.com/devsecblueprint/devsecblueprint/blob/main/LICENSE",
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} The DevSec Blueprint`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
    zoom: {
      selector: ".markdown :not(em) > img",
      config: {
        // options you can specify via https://github.com/francoischalifour/medium-zoom#usage
        background: {
          light: "rgb(255, 255, 255)",
          dark: "rgb(50, 50, 50)",
        },
      },
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
