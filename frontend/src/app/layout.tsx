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
          {/* Mobile notice — visible only on small screens */}
          <div className="sm:hidden fixed inset-0 z-[100] bg-bg-primary flex items-center justify-center p-6">
            <div className="text-center max-w-xs">
              <div className="w-10 h-10 rounded-full bg-accent-cyan/20 flex items-center justify-center mx-auto mb-4">
                <div className="w-4 h-4 rounded-full bg-accent-cyan" />
              </div>
              <h2 className="text-lg font-semibold mb-2">GPS Shield</h2>
              <p className="text-text-muted text-sm">
                This interactive research platform is best experienced on a desktop or tablet.
                The 3D globe and data visualizations require a larger screen.
              </p>
            </div>
          </div>
          <main className="relative">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
