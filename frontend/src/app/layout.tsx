import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { Nav } from "@/components/ui";

/**
 * Root metadata for GPS Shield.
 * Sets page title and description for the entire app.
 */
export const metadata: Metadata = {
  title: "GPS Shield — GPS Anomaly Detection Engine",
  description:
    "Analyzing millions of flight records to map the GPS spoofing crisis and model how next-generation LEO navigation solves it.",
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
          {/* Mobile notice — banner instead of full overlay */}
          <div className="sm:hidden fixed top-0 left-0 right-0 z-[100] bg-bg-surface border-b border-border-subtle px-4 py-3 text-center">
            <p className="text-text-muted text-xs">
              Best experienced on desktop. The 3D globe requires a larger screen.
            </p>
          </div>
          <main className="relative">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
