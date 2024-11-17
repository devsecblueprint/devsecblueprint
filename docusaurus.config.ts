import { themes as prismThemes } from "prism-react-renderer";
import type { Config } from "@docusaurus/types";
import type * as Preset from "@docusaurus/preset-classic";

const config: Config = {
  title: "DSB",
  tagline: "DevSec Blueprint",
  favicon: "img/logo.svg",

  // Set the production url of your site here
  url: "https://devsecblueprint.github.io",
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: "/",

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: "The-DevSec-Blueprint", // Usually your GitHub org/user name.
  projectName: "devsecblueprint", // Usually your repo name.

  onBrokenLinks: "throw",
  onBrokenMarkdownLinks: "warn",

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en', // Default language of your site
    locales: [
      'en',      // English
      'es',      // Spanish
      'fr',      // French
      'de',      // German
      'it',      // Italian
      'zh-CN',   // Chinese (Simplified)
      'zh-TW',   // Chinese (Traditional)
      'ja',      // Japanese
      'ko',      // Korean
      'pt-BR',   // Portuguese (Brazil)
      'pt-PT',   // Portuguese (Portugal)
      'ru',      // Russian
      'ar',      // Arabic
      'hi',      // Hindi
      'bn',      // Bengali
      'tr',      // Turkish
      'vi',      // Vietnamese
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
          type: 'localeDropdown',
          position: 'right', // Position of the language switcher in the navbar
        },
        {
          href: "https://github.com/The-DevSec-Blueprint/devsecblueprint.github.io",
          position: "right",
          className: "header-github-link",
          "aria-label": "GitHub Repository",
        },
      ],
    },
    announcementBar: {
      id: "announcement", // Any unique ID
      content:
        "🌟 If you like what you see, give the DSB a STAR and share with friends!",
      backgroundColor: "#fafbfc", // Defaults to `#fff`
      textColor: "#091E42", // Defaults to `#000`
      isCloseable: true, // Defaults to `true`
    },
    footer: {
      style: "dark",
      links: [
        {
          title: "Socials",
          items: [
            {
              label: "Discord",
              href: "https://discordapp.com/invite/dummy",
            },
            {
              label: "LinkedIn",
              href: "https://www.linkedin.com/company/devsecblueprint/",
            },
          ],
        },
        {
          title: "Blueprint Help",
          items: [
            {
              label: "Report Issue",
              href: "https://github.com/The-DevSec-Blueprint/devsecblueprint.github.io/issues",
            },
            {
              label: "GitHub Repository",
              href: "https://github.com/The-DevSec-Blueprint/devsecblueprint.github.io",
            },
          ],
        },
        {
          title: "Community",
          items: [
            {
              label: "Code Of Conduct",
              href: "https://github.com/The-DevSec-Blueprint/devsecblueprint.github.io/blob/main/CODE_OF_CONDUCT.md/",
            },
            {
              label: "License",
              href: "https://github.com/The-DevSec-Blueprint/devsecblueprint.github.io/blob/main/LICENSE",
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
