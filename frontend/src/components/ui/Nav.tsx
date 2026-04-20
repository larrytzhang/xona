"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { clsx } from "clsx";
import { Globe, BarChart3, Shield, HelpCircle } from "lucide-react";
import { WelcomeModal } from "./WelcomeModal";

interface NavLink {
  href: string;
  label: string;
  icon: React.ReactNode;
}

const NAV_LINKS: NavLink[] = [
  { href: "/", label: "Globe", icon: <Globe size={16} /> },
  { href: "/findings", label: "Findings", icon: <BarChart3 size={16} /> },
  { href: "/pulsar", label: "Pulsar", icon: <Shield size={16} /> },
];

const GITHUB_URL =
  process.env.NEXT_PUBLIC_GITHUB_URL || "https://github.com/larrytzhang/xona";

/**
 * Top navigation bar for GPS Shield.
 *
 * Renders the logo, primary page links, and secondary actions (help
 * modal trigger + external GitHub link). Highlights the active route.
 */
export function Nav() {
  const pathname = usePathname();
  const [helpOpen, setHelpOpen] = useState(false);

  return (
    <>
      <nav className="fixed top-0 left-0 right-0 z-50 glass h-14 flex items-center px-4 md:px-6 border-b border-border-subtle">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 mr-4 md:mr-8 group" aria-label="GPS Shield home">
          <span className="relative flex items-center justify-center w-6 h-6 rounded-full bg-accent-cyan/20">
            <span className="absolute inset-0 rounded-full bg-accent-cyan/20 group-hover:animate-ping" />
            <span className="relative w-2.5 h-2.5 rounded-full bg-accent-cyan" />
          </span>
          <span className="font-semibold text-sm tracking-wide">GPS SHIELD</span>
        </Link>

        {/* Primary links */}
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
                  "flex items-center gap-1.5 px-2.5 md:px-3 py-1.5 rounded-md text-sm transition-colors",
                  isActive
                    ? "bg-accent-cyan/10 text-accent-cyan"
                    : "text-text-secondary hover:text-text-primary hover:bg-bg-elevated"
                )}
                aria-current={isActive ? "page" : undefined}
              >
                {link.icon}
                <span className="hidden sm:inline">{link.label}</span>
              </Link>
            );
          })}
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Secondary actions */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => setHelpOpen(true)}
            aria-label="Open how-to-use guide"
            className="p-2 rounded-md text-text-secondary hover:text-text-primary hover:bg-bg-elevated transition-colors"
          >
            <HelpCircle size={16} />
          </button>
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="View source on GitHub"
            className="p-2 rounded-md text-text-secondary hover:text-text-primary hover:bg-bg-elevated transition-colors"
          >
            <svg width={16} height={16} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M12 .5C5.7.5.5 5.7.5 12c0 5.1 3.3 9.4 7.9 10.9.6.1.8-.3.8-.6v-2c-3.2.7-3.9-1.5-3.9-1.5-.5-1.3-1.3-1.7-1.3-1.7-1-.7.1-.7.1-.7 1.2.1 1.8 1.2 1.8 1.2 1 1.8 2.8 1.3 3.5 1 .1-.8.4-1.3.8-1.6-2.6-.3-5.3-1.3-5.3-5.7 0-1.3.5-2.3 1.2-3.2-.1-.3-.5-1.5.1-3.1 0 0 1-.3 3.3 1.2a11 11 0 016 0c2.3-1.5 3.3-1.2 3.3-1.2.6 1.6.2 2.8.1 3.1.8.9 1.2 1.9 1.2 3.2 0 4.5-2.7 5.4-5.3 5.7.4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6A11.5 11.5 0 0023.5 12C23.5 5.7 18.3.5 12 .5z" />
            </svg>
          </a>
        </div>
      </nav>

      {helpOpen && <WelcomeModal forceOpen onClose={() => setHelpOpen(false)} />}
    </>
  );
}
