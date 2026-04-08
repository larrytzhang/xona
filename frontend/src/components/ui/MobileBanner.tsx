"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";
import { X } from "lucide-react";

/**
 * Dismissible mobile notice shown only on the globe page (/).
 * The Findings and Pulsar pages work fine on mobile, so no warning needed there.
 */
export function MobileBanner() {
  const [dismissed, setDismissed] = useState(false);
  const pathname = usePathname();

  // Only show on the globe page
  if (pathname !== "/" || dismissed) return null;

  return (
    <div className="sm:hidden fixed top-14 left-0 right-0 z-[100] bg-bg-surface border-b border-border-subtle px-4 py-2 flex items-center justify-between">
      <p className="text-text-muted text-xs flex-1">
        Best experienced on desktop. The 3D globe requires a larger screen.
      </p>
      <button
        onClick={() => setDismissed(true)}
        className="ml-2 p-1 text-text-muted hover:text-text-primary transition-colors"
        aria-label="Dismiss mobile notice"
      >
        <X size={14} />
      </button>
    </div>
  );
}
