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
    image: "img/og-icon.jpg",
    metadata: [
      {
        name: "keywords",
        content: "DevSecOps, DevOps, Cyber Security, Cloud Security, DevSecBlueprint",
      },

      // Open Graph / Facebook
      { property: "og:type", content: "website" },
      { property: "og:site_name", content: "DevSec Blueprint" },
      {
        property: "og:title",
        content: "The DevSec Blueprint - Learn DevSecOps & Cloud Security",
      },
      {
        property: "og:description",
        content:
          "Free and open-source learning platform to help engineers learn, build, and grow in DevSecOps and Cloud Security. From foundational theory to hands-on cloud labs.",
      },
      { property: "og:url", content: "https://devsecblueprint.com" },
      {
        property: "og:image",
        content: "https://devsecblueprint.com/img/og-icon.jpg",
      },
      {
        property: "og:logo",
        content: "https://devsecblueprint.com/img/og-icon.jpg",
      },
      { property: "og:image:alt", content: "DevSec Blueprint Logo" },
      { property: "og:image:width", content: "1200" },
      { property: "og:image:height", content: "630" },
      { property: "og:locale", content: "en_US" },

      // Twitter Card
      { name: "twitter:card", content: "summary_large_image" },
      { name: "twitter:site", content: "@devsecblueprint" },
      { name: "twitter:creator", content: "@devsecblueprint" },
      {
        name: "twitter:title",
        content: "The DevSec Blueprint - Learn DevSecOps & Cloud Security",
      },
      {
        name: "twitter:description",
        content:
          "Free and open-source learning platform to help engineers learn, build, and grow in DevSecOps and Cloud Security.",
      },
      {
        name: "twitter:image",
        content: "https://devsecblueprint.com/img/og-icon.jpg",
      },
    ],
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
          href: "https://shop.devsecblueprint.com",
          label: "SWAG Shop",
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
        '<a href="https://www.youtube.com/watch?v=1-OMoEbhr7g&t=1s" target="_blank" rel="noopener noreferrer"><b>How to Start a Career in DevSecOps in 2025!</b></a> 🔒',
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
              label: "Contributing",
              href: "https://github.com/devsecblueprint/devsecblueprint/blob/main/CONTRIBUTING.md",
            },
            {
              href: "https://shop.devsecblueprint.com",
              label: "SWAG Shop",
            },
            {
              label: "License",
              href: "https://github.com/devsecblueprint/devsecblueprint/blob/main/LICENSE",
            },
          ],
        },
      ],
      copyright: `Made with ❤️ using <strong><span style="color: #4fd1c7;">Docusaurus</span></strong> and a <span style="font-style: italic;">sprinkle</span> of <strong><span style="color: #a78bfa;">Kiro</span></strong>. Powered by <strong><span style="color: #ffa726;">AWS</span></strong> <br/>Copyright ©${new Date().getFullYear()} DevSec Blueprint LLC`,
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
