"use client";

import { SignalComparison, RadiusAnimation, AuthExplainer } from "@/components/pulsar";

/**
 * Pulsar Explainer page — how Xona's constellation solves GPS vulnerability.
 *
 * Three sections explaining Pulsar's advantages:
 *   1. Signal Strength — ~178x more received power than GPS.
 *   2. Jamming Radius — 97.5% area reduction.
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

      {/* How It Works — detection pipeline overview */}
      <div className="glass rounded-xl p-6 mt-8">
        <h2 className="text-xl font-bold mb-4">How the Detection Works</h2>
        <p className="text-text-secondary text-sm mb-4">
          GPS Shield analyzes ADS-B aircraft position reports through a multi-stage
          anomaly detection pipeline to identify GPS spoofing and jamming events.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="space-y-3">
            <div>
              <p className="text-text-primary font-medium">1. Data Ingestion</p>
              <p className="text-text-muted">Aircraft state vectors (position, velocity, altitude, heading) are collected from the OpenSky Network.</p>
            </div>
            <div>
              <p className="text-text-primary font-medium">2. Per-Aircraft Detection</p>
              <p className="text-text-muted">Six detectors analyze each aircraft: impossible velocity, position teleportation, baro/geo altitude divergence, heading vs trajectory mismatch, spatial clustering, and coordinated signal loss.</p>
            </div>
            <div>
              <p className="text-text-primary font-medium">3. Classification</p>
              <p className="text-text-muted">A decision tree classifies each anomaly as spoofing (fake signals), jamming (signal denial), or unclassified based on which detectors fired and their confidence levels.</p>
            </div>
          </div>
          <div className="space-y-3">
            <div>
              <p className="text-text-primary font-medium">4. Severity Scoring</p>
              <p className="text-text-muted">Each anomaly receives a 0-100 severity score based on detector confidence (35%), flag count (15%), cluster size (25%), persistence (15%), and altitude risk (10%).</p>
            </div>
            <div>
              <p className="text-text-primary font-medium">5. Spatial Clustering</p>
              <p className="text-text-muted">DBSCAN groups nearby anomalies (within 150 km, 3+ aircraft) into interference zones. Clustered anomalies are re-scored with context.</p>
            </div>
            <div>
              <p className="text-text-primary font-medium">6. Pulsar Modeling</p>
              <p className="text-text-muted">Each zone is modeled with Pulsar mitigation: spoofing is eliminated via cryptographic authentication, and jamming radii shrink by 97.5% due to the 6.3x signal advantage.</p>
            </div>
          </div>
        </div>
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
