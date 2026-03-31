import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { Nav } from "@/components/ui/Nav";

/**
 * Root metadata for GPS Shield.
 * Sets page title, description, and theme color for the entire app.
 */
export const metadata: Metadata = {
  title: "GPS Shield — GPS Anomaly Detection Engine",
  description:
    "Analyzing millions of flight records to map the GPS spoofing crisis and model how next-generation LEO navigation solves it.",
  themeColor: "#09090B",
};

/**
 * Root layout wrapping all pages.
 *
 * Provides:
 *   - Dark background theme.
 *   - React Query provider for data fetching.
 *   - Top navigation bar.
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
          <main className="relative">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
