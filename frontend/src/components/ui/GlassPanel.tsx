"use client";

import { clsx } from "clsx";

/**
 * Reusable glass morphism container panel.
 *
 * Renders a frosted-glass style container with subtle border,
 * backdrop blur, and dark semi-transparent background. Used
 * throughout the dashboard for stats, sidebars, and overlays.
 *
 * @param children - Content to render inside the panel.
 * @param className - Additional CSS classes to apply.
 * @returns A styled div with glass morphism effect.
 */
export function GlassPanel({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={clsx(
        "glass rounded-xl shadow-lg",
        className
      )}
    >
      {children}
    </div>
  );
}
