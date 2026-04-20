"use client";

import { useCallback, useEffect, useState } from "react";
import { X, Globe, Shield, BarChart3 } from "lucide-react";

const STORAGE_KEY = "gpsshield.welcomed.v1";

/**
 * First-visit welcome modal introducing the demo in three steps.
 *
 * Persists a dismissal flag in localStorage so the modal only appears
 * once per browser. Can be reopened via the "?" help button in the nav.
 */
export function WelcomeModal({
  forceOpen,
  onClose,
}: {
  forceOpen?: boolean;
  onClose?: () => void;
}) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (forceOpen) {
      setOpen(true);
      return;
    }
    // Only run on the client. Show if user has never dismissed.
    try {
      const dismissed = window.localStorage.getItem(STORAGE_KEY) === "1";
      if (!dismissed) setOpen(true);
    } catch {
      // localStorage disabled — show once per session instead.
      setOpen(true);
    }
  }, [forceOpen]);

  const handleClose = useCallback(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, "1");
    } catch {
      // ignore
    }
    setOpen(false);
    onClose?.();
  }, [onClose]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") handleClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, handleClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in-up"
      role="dialog"
      aria-modal="true"
      aria-labelledby="welcome-title"
      onClick={handleClose}
    >
      <div
        className="glass rounded-2xl max-w-lg w-full p-6 md:p-8 relative"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={handleClose}
          aria-label="Close welcome"
          className="absolute top-4 right-4 p-1 rounded hover:bg-bg-elevated transition-colors text-text-muted"
        >
          <X size={18} />
        </button>

        <div className="flex items-center gap-2 mb-3">
          <div className="w-8 h-8 rounded-full bg-accent-cyan/20 flex items-center justify-center">
            <div className="w-3 h-3 rounded-full bg-accent-cyan" />
          </div>
          <span className="text-xs font-medium tracking-wider text-accent-cyan uppercase">
            GPS Shield
          </span>
        </div>

        <h2 id="welcome-title" className="text-2xl font-bold mb-2">
          Map the GPS spoofing crisis.
        </h2>
        <p className="text-text-secondary text-sm mb-6 leading-relaxed">
          A research demo that detects GPS interference worldwide and models how
          Xona&apos;s Pulsar constellation would neutralize each threat. Three
          things to try:
        </p>

        <ol className="space-y-3 mb-6">
          <Step
            icon={<Globe size={16} className="text-accent-cyan" />}
            title="Explore the globe"
            body="Click a glowing zone to see affected aircraft, severity, and Pulsar mitigation."
          />
          <Step
            icon={<Shield size={16} className="text-accent-cyan" />}
            title="Toggle Pulsar Mode"
            body="Watch jamming radii collapse by 97.5% and spoofing disappear entirely."
          />
          <Step
            icon={<BarChart3 size={16} className="text-accent-cyan" />}
            title="Check the Findings"
            body="Pre-computed insights across 7 conflict zones, with data transparency."
          />
        </ol>

        <div className="flex items-center justify-between gap-3">
          <span className="text-[11px] text-text-muted">
            Synthetic demo data · Press <kbd className="px-1.5 py-0.5 rounded bg-bg-elevated border border-border-subtle font-mono-numbers text-[10px]">Esc</kbd> to close
          </span>
          <button
            onClick={handleClose}
            className="px-4 py-2 rounded-lg bg-accent-cyan text-bg-primary text-sm font-medium hover:bg-accent-cyan/90 transition-colors"
          >
            Start the tour
          </button>
        </div>
      </div>
    </div>
  );
}

function Step({
  icon,
  title,
  body,
}: {
  icon: React.ReactNode;
  title: string;
  body: string;
}) {
  return (
    <li className="flex items-start gap-3">
      <div className="w-8 h-8 flex-shrink-0 rounded-lg bg-bg-elevated flex items-center justify-center mt-0.5">
        {icon}
      </div>
      <div>
        <div className="text-sm font-medium text-text-primary">{title}</div>
        <div className="text-xs text-text-secondary leading-relaxed">{body}</div>
      </div>
    </li>
  );
}
