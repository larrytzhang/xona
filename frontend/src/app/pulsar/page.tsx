"use client";

import { SignalComparison, RadiusAnimation, AuthExplainer } from "@/components/pulsar";

/**
 * Pulsar Explainer page — how Xona's constellation solves GPS vulnerability.
 *
 * Three sections explaining Pulsar's advantages:
 *   1. Signal Strength — 100x more power than GPS.
 *   2. Jamming Radius — 97% area reduction.
 *   3. Spoofing Immunity — cryptographic range authentication.
 *
 * Uses the project's own analysis data as evidence.
 */
export default function PulsarPage() {
  return (
    <div className="min-h-screen pt-20 pb-16 px-6 max-w-4xl mx-auto">
      {/* Hero */}
      <div className="mb-10">
        <h1 className="text-3xl font-bold mb-2">How Pulsar Works</h1>
        <p className="text-text-secondary">
          Xona Space Systems is building Pulsar — a Low Earth Orbit navigation
          constellation designed to be resilient against the GPS threats
          identified in our analysis.
        </p>
      </div>

      {/* Three sections */}
      <div className="space-y-8">
        <SignalComparison />
        <RadiusAnimation />
        <AuthExplainer />
      </div>

      {/* Footer link */}
      <div className="mt-12 text-center text-sm text-text-muted">
        Learn more about Xona Space Systems at{" "}
        <a
          href="https://www.xonaspace.com"
          target="_blank"
          rel="noopener noreferrer"
          className="text-accent-cyan hover:underline"
        >
          xonaspace.com
        </a>
      </div>
    </div>
  );
}
