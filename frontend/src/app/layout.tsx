import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { Nav } from "@/components/ui";
import { MobileBanner } from "@/components/ui/MobileBanner";

/**
 * Root metadata for GPS Shield.
 * Sets page title and description for the entire app.
 */
export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"),
  title: "GPS Shield — GPS Anomaly Detection Engine",
  description:
    "Analyzing millions of flight records to map the GPS spoofing crisis and model how next-generation LEO navigation solves it.",
  openGraph: {
    title: "GPS Shield — GPS Anomaly Detection Engine",
    description:
      "Detecting GPS spoofing and jamming across 7 conflict zones. Toggle Pulsar Mode to see how Xona's LEO constellation would neutralize each threat.",
    type: "website",
    images: ["/og-image.png"],
  },
};

/**
 * Viewport configuration with dark theme color and responsive width.
 */
export const viewport: Viewport = {
  themeColor: "#09090B",
  width: "device-width",
  initialScale: 1,
};

/**
 * Root layout wrapping all pages.
 *
 * Provides:
 *   - Dark background theme.
 *   - React Query provider for data fetching.
 *   - Top navigation bar.
 *   - Mobile notice for small screens (globe requires desktop).
 *
 * @param children - Page content rendered by Next.js App Router.
 * @returns The root HTML structure with providers and nav.
 */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-bg-primary text-text-primary antialiased min-h-screen">
        <Providers>
          <Nav />
          <MobileBanner />
          <main className="relative">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
