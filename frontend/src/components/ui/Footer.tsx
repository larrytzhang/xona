import Link from "next/link";
import { Mail, FileCode } from "lucide-react";

const GITHUB_URL =
  process.env.NEXT_PUBLIC_GITHUB_URL || "https://github.com/larrytzhang/xona";
const LINKEDIN_URL =
  process.env.NEXT_PUBLIC_LINKEDIN_URL || "https://www.linkedin.com/in/larryzhang225/";
const CONTACT_EMAIL = process.env.NEXT_PUBLIC_CONTACT_EMAIL || "larry_zhang@college.harvard.edu";
const API_DOCS_URL =
  (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") + "/docs";

/**
 * Sitewide footer with creator credit, methodology link, and source links.
 *
 * Rendered inside page content (not fixed) so it appears at the bottom of
 * scrollable pages. The Globe page skips the footer because it is full-bleed.
 */
export function Footer() {
  return (
    <footer className="border-t border-border-subtle mt-16 px-6 py-8 text-sm text-text-muted">
      <div className="max-w-5xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="text-text-primary font-medium">Built by Larry Zhang</div>
        </div>

        <div className="flex flex-wrap items-center gap-4 text-xs">
          <Link
            href="/methodology"
            className="hover:text-text-primary transition-colors inline-flex items-center gap-1.5"
          >
            <FileCode size={14} />
            Methodology
          </Link>
          <a
            href={API_DOCS_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-text-primary transition-colors"
          >
            API docs
          </a>
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="GitHub"
            className="hover:text-text-primary transition-colors inline-flex items-center gap-1.5"
          >
            <GithubIcon /> GitHub
          </a>
          <a
            href={LINKEDIN_URL}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="LinkedIn"
            className="hover:text-text-primary transition-colors inline-flex items-center gap-1.5"
          >
            <LinkedinIcon /> LinkedIn
          </a>
          <a
            href={`mailto:${CONTACT_EMAIL}`}
            className="hover:text-text-primary transition-colors inline-flex items-center gap-1.5"
          >
            <Mail size={14} /> Email
          </a>
        </div>
      </div>
    </footer>
  );
}

function GithubIcon() {
  return (
    <svg width={14} height={14} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 .5C5.7.5.5 5.7.5 12c0 5.1 3.3 9.4 7.9 10.9.6.1.8-.3.8-.6v-2c-3.2.7-3.9-1.5-3.9-1.5-.5-1.3-1.3-1.7-1.3-1.7-1-.7.1-.7.1-.7 1.2.1 1.8 1.2 1.8 1.2 1 1.8 2.8 1.3 3.5 1 .1-.8.4-1.3.8-1.6-2.6-.3-5.3-1.3-5.3-5.7 0-1.3.5-2.3 1.2-3.2-.1-.3-.5-1.5.1-3.1 0 0 1-.3 3.3 1.2a11 11 0 016 0c2.3-1.5 3.3-1.2 3.3-1.2.6 1.6.2 2.8.1 3.1.8.9 1.2 1.9 1.2 3.2 0 4.5-2.7 5.4-5.3 5.7.4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6A11.5 11.5 0 0023.5 12C23.5 5.7 18.3.5 12 .5z" />
    </svg>
  );
}

function LinkedinIcon() {
  return (
    <svg width={14} height={14} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M20.5 2h-17A1.5 1.5 0 002 3.5v17A1.5 1.5 0 003.5 22h17a1.5 1.5 0 001.5-1.5v-17A1.5 1.5 0 0020.5 2zM8 19H5v-9h3v9zM6.5 8.3a1.8 1.8 0 110-3.6 1.8 1.8 0 010 3.6zM19 19h-3v-4.8c0-1.2 0-2.7-1.7-2.7s-1.9 1.3-1.9 2.6V19h-3v-9h2.9v1.2h.1a3.2 3.2 0 012.8-1.5c3 0 3.6 2 3.6 4.5V19z" />
    </svg>
  );
}
