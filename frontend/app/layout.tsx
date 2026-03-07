import type { Metadata } from "next";
import "@/styles/globals.css";
import { Providers } from "@/components/Providers";
import { ScrollRestoration } from "@/components/ScrollRestoration";
import { GoogleAnalytics } from "@/components/GoogleAnalytics";

export const metadata: Metadata = {
  title: "The DevSec Blueprint",
  description: "Structured DevSecOps and Cloud Security mastery. Built through real systems, not theory.",
  icons: {
    icon: [
      { url: '/dark_mode_logo.svg', type: 'image/svg+xml' },
    ],
  },
  openGraph: {
    title: "The DevSec Blueprint",
    description: "Structured DevSecOps and Cloud Security mastery. Built through real systems, not theory.",
    url: "https://staging.devsecblueprint.com",
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
  },
  metadataBase: new URL("https://staging.devsecblueprint.com"),
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
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
