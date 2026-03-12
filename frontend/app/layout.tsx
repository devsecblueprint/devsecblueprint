import type { Metadata } from "next";
import "@/styles/globals.css";
import { Providers } from "@/components/Providers";
import { ScrollRestoration } from "@/components/ScrollRestoration";
import { GoogleAnalytics } from "@/components/GoogleAnalytics";

export const metadata: Metadata = {
  title: {
    default: "The DevSec Blueprint",
    template: "%s | The DevSec Blueprint",
  },
  description: "Structured DevSecOps and Cloud Security mastery. Built through real systems, not theory.",
  keywords: ["DevSecOps", "Cloud Security", "Cybersecurity", "AWS", "Azure", "GCP", "Security Engineering", "DevOps", "Application Security"],
  authors: [{ name: "DevSec Blueprint Team" }],
  creator: "DevSec Blueprint",
  publisher: "DevSec Blueprint LLC",
  icons: {
    icon: [
      { url: '/dark_mode_logo.svg', type: 'image/svg+xml' },
    ],
  },
  openGraph: {
    title: "The DevSec Blueprint",
    description: "Structured DevSecOps and Cloud Security mastery. Built through real systems, not theory.",
    url: "https://devsecblueprint.com",
    siteName: "The DevSec Blueprint",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "The DevSec Blueprint - DevSecOps and Cloud Security Learning Platform",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "The DevSec Blueprint",
    description: "Structured DevSecOps and Cloud Security mastery. Built through real systems, not theory.",
    images: ["/og-image.png"],
    creator: "@devsecblueprint",
    site: "@devsecblueprint",
  },
  metadataBase: new URL("https://devsecblueprint.com"),
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  verification: {
    google: "xHeqrDv2asGBQ_nD-v1VeMVG6BtaNjzk0Do7uEvzumw",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  const savedTheme = localStorage.getItem('theme');
                  const theme = savedTheme || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
                  if (theme === 'dark') {
                    document.documentElement.classList.add('dark');
                  } else {
                    document.documentElement.classList.remove('dark');
                  }
                } catch (e) {}
              })();
            `,
          }}
        />
        <style
          dangerouslySetInnerHTML={{
            __html: `
              /* Prevent flash of wrong theme */
              html:not(.dark) {
                color-scheme: light;
              }
              html.dark {
                color-scheme: dark;
              }
            `,
          }}
        />
      </head>
      <body className="bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100 antialiased transition-colors">
        <GoogleAnalytics />
        <Providers>
          <ScrollRestoration />
          {children}
        </Providers>
      </body>
    </html>
  );
}
