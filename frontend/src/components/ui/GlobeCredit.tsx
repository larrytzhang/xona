const GITHUB_URL =
  process.env.NEXT_PUBLIC_GITHUB_URL || "https://github.com/larrytzhang/xona";
const LINKEDIN_URL =
  process.env.NEXT_PUBLIC_LINKEDIN_URL || "https://www.linkedin.com/in/larryzhang225/";

/**
 * Compact creator credit shown on the full-bleed Globe page.
 *
 * The regular Footer would clash with the full-screen globe, so this
 * component floats a minimal credit + key links in the bottom-left.
 */
export function GlobeCredit() {
  return (
    <div className="hidden md:flex absolute bottom-3 left-3 z-30 glass rounded-md px-2.5 py-1.5 items-center gap-2 text-[10px] text-text-muted">
      <span className="text-text-secondary">Built by Larry Zhang</span>
      <span aria-hidden="true">·</span>
      <a
        href={GITHUB_URL}
        target="_blank"
        rel="noopener noreferrer"
        className="hover:text-text-primary transition-colors"
      >
        GitHub
      </a>
      <span aria-hidden="true">·</span>
      <a
        href={LINKEDIN_URL}
        target="_blank"
        rel="noopener noreferrer"
        className="hover:text-text-primary transition-colors"
      >
        LinkedIn
      </a>
      <span aria-hidden="true">·</span>
      <a href="/methodology" className="hover:text-text-primary transition-colors">
        Methodology
      </a>
    </div>
  );
}
