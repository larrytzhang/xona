"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";
import { Globe, BarChart3, Shield } from "lucide-react";

/**
 * Navigation link item definition.
 */
interface NavLink {
  href: string;
  label: string;
  icon: React.ReactNode;
}

/** Navigation links for the three main views. */
const NAV_LINKS: NavLink[] = [
  { href: "/", label: "Globe", icon: <Globe size={16} /> },
  { href: "/findings", label: "Findings", icon: <BarChart3 size={16} /> },
  { href: "/pulsar", label: "How Pulsar Works", icon: <Shield size={16} /> },
];

/**
 * Top navigation bar for GPS Shield.
 *
 * Displays the app name and links to the three main views:
 * Globe (home), Key Findings, and Pulsar Explainer.
 * Highlights the active page link.
 *
 * @returns The fixed top navigation bar component.
 */
export function Nav() {
  const pathname = usePathname();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass h-14 flex items-center px-6 border-b border-border-subtle">
      {/* Logo / App Name */}
      <Link href="/" className="flex items-center gap-2 mr-8">
        <div className="w-6 h-6 rounded-full bg-accent-cyan/20 flex items-center justify-center">
          <div className="w-2.5 h-2.5 rounded-full bg-accent-cyan" />
        </div>
        <span className="font-semibold text-sm tracking-wide">GPS SHIELD</span>
      </Link>

      {/* Navigation Links */}
      <div className="flex items-center gap-1">
        {NAV_LINKS.map((link) => {
          const isActive =
            link.href === "/"
              ? pathname === "/"
              : pathname.startsWith(link.href);

          return (
            <Link
              key={link.href}
              href={link.href}
              className={clsx(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors",
                isActive
                  ? "bg-accent-cyan/10 text-accent-cyan"
                  : "text-text-secondary hover:text-text-primary hover:bg-bg-elevated"
              )}
            >
              {link.icon}
              {link.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
