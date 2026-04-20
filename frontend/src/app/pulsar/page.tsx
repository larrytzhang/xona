"use client";

import {
  SignalComparison,
  RadiusAnimation,
  AuthExplainer,
  JammerSandbox,
} from "@/components/pulsar";
import { Footer } from "@/components/ui";

/**
 * Pulsar Explainer page — how Xona's constellation solves GPS vulnerability.
 *
 * Structure:
 *   1. Hero
 *   2. Try it yourself — draggable jammer sandbox (hands-on demo)
 *   3. Signal strength chart (~178x advantage)
 *   4. Jamming radius animation (97.5% area reduction)
 *   5. Cryptographic authentication explainer
 *   6. How the detection pipeline works
 *   7. Footer
 */
export default function PulsarPage() {
  return (
    <>
      <div className="min-h-screen pt-20 pb-8 px-4 md:px-6 max-w-4xl mx-auto">
        {/* Hero */}
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-bold mb-2 tracking-tight">
            How Pulsar Works
          </h1>
          <p className="text-text-secondary leading-relaxed max-w-2xl">
            Xona Space Systems is building Pulsar — a Low Earth Orbit navigation
            constellation designed to be resilient against the GPS threats
            identified in our analysis. Try the simulator, then see the physics.
          </p>
        </div>

        {/* Interactive sandbox — anchors the whole page */}
        <div className="mb-8">
          <JammerSandbox />
        </div>

        {/* Three explainer sections */}
        <div className="space-y-6">
          <SignalComparison />
          <RadiusAnimation />
          <AuthExplainer />
        </div>

        {/* How It Works — detection pipeline overview */}
        <div className="glass rounded-xl p-6 md:p-8 mt-8">
          <h2 className="text-xl font-bold mb-4">How the Detection Works</h2>
          <p className="text-text-secondary text-sm mb-5 leading-relaxed">
            GPS Shield analyzes ADS-B aircraft position reports through a
            multi-stage anomaly detection pipeline to identify GPS spoofing
            and jamming events.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 text-sm">
            <div className="space-y-3">
              <StepRow
                num="1"
                title="Data Ingestion"
                body="Aircraft state vectors (position, velocity, altitude, heading) are collected from the OpenSky Network."
              />
              <StepRow
                num="2"
                title="Per-Aircraft Detection"
                body="Six detectors analyze each aircraft: impossible velocity, position teleportation, baro/geo altitude divergence, heading vs trajectory mismatch, spatial clustering, and coordinated signal loss."
              />
              <StepRow
                num="3"
                title="Classification"
                body="A decision tree classifies each anomaly as spoofing (fake signals), jamming (signal denial), or unclassified based on which detectors fired and their confidence levels."
              />
            </div>
            <div className="space-y-3">
              <StepRow
                num="4"
                title="Severity Scoring"
                body="Each anomaly receives a 0-100 severity score based on detector confidence (35%), flag count (15%), cluster size (25%), persistence (15%), and altitude risk (10%)."
              />
              <StepRow
                num="5"
                title="Spatial Clustering"
                body="DBSCAN groups nearby anomalies (within 150 km, 3+ aircraft) into interference zones. Clustered anomalies are re-scored with context."
              />
              <StepRow
                num="6"
                title="Pulsar Modeling"
                body="Each zone is modeled with Pulsar mitigation: spoofing is eliminated via cryptographic authentication, and jamming radii shrink by 97.5% due to the 6.3x signal advantage."
              />
            </div>
          </div>
        </div>
      </div>

      <Footer />
    </>
  );
}

function StepRow({ num, title, body }: { num: string; title: string; body: string }) {
  return (
    <div className="flex gap-3">
      <div className="flex-shrink-0 w-6 h-6 rounded-full bg-accent-cyan/15 text-accent-cyan text-xs font-mono-numbers font-medium flex items-center justify-center mt-0.5">
        {num}
      </div>
      <div>
        <p className="text-text-primary font-medium leading-tight mb-1">{title}</p>
        <p className="text-text-muted leading-relaxed">{body}</p>
      </div>
    </div>
  );
}
