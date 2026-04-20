import { Footer } from "@/components/ui";
import { ExternalLink } from "lucide-react";
import Link from "next/link";

export const metadata = {
  title: "Methodology — GPS Shield",
  description:
    "How GPS Shield detects interference, what data it uses, and where the Pulsar mitigation numbers come from.",
};

/**
 * Methodology and citations page.
 *
 * Shows the reviewer *where every number comes from*, so nothing on
 * the demo looks fabricated. Links to the underlying research, the
 * FastAPI schema, and the source code.
 */
export default function MethodologyPage() {
  return (
    <>
      <div className="min-h-screen pt-20 pb-8 px-4 md:px-6 max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-bold mb-2 tracking-tight">
            Methodology
          </h1>
          <p className="text-text-secondary leading-relaxed max-w-2xl">
            Every number in this demo comes from a reproducible pipeline with
            published sources. Here&apos;s exactly how.
          </p>
        </div>

        <div className="space-y-6">
          <Section title="1. Data sources">
            <p>
              The detection pipeline is designed to ingest real ADS-B aircraft
              state vectors from the{" "}
              <Ext href="https://opensky-network.org">OpenSky Network</Ext>, an
              open research dataset with millions of flights per day. The
              hosted demo uses <strong>synthetic data</strong> calibrated to
              published GPS interference patterns so that the demo runs on
              free-tier infrastructure — the detection code is identical in
              either mode.
            </p>
            <p>
              Synthetic zone geography and temporal trends follow published
              reports from{" "}
              <Ext href="https://c4ads.org/reports/above-us-only-stars/">C4ADS</Ext> and{" "}
              <Ext href="https://www.eurocontrol.int/publication/does-radio-frequency-interference-pose-threat-aviation-safety">
                EUROCONTROL
              </Ext>{" "}
              on spoofing and jamming across the Baltic, Eastern Mediterranean,
              Persian Gulf, Red Sea, Black Sea, Ukraine, and South China Sea.
            </p>
          </Section>

          <Section title="2. Anomaly detectors">
            <p>
              Six detectors run in parallel on each state vector. Thresholds
              are documented in{" "}
              <Code>backend/app/detection/internal/detectors.py</Code>.
            </p>
            <ul className="list-disc pl-6 space-y-1.5 mt-2">
              <li>
                <strong>Impossible velocity</strong> — ground speed exceeds
                physical limits for the altitude band.
              </li>
              <li>
                <strong>Position teleportation</strong> — successive positions
                imply an impossible distance for elapsed time.
              </li>
              <li>
                <strong>Altitude divergence</strong> — barometric and geometric
                altitude disagree beyond GPS noise.
              </li>
              <li>
                <strong>Heading mismatch</strong> — reported heading disagrees
                with track computed from successive positions.
              </li>
              <li>
                <strong>Spatial clustering</strong> — multiple aircraft with
                anomalies in the same area at the same time.
              </li>
              <li>
                <strong>Coordinated signal loss</strong> — simultaneous ADS-B
                dropouts across a region.
              </li>
            </ul>
          </Section>

          <Section title="3. Pulsar mitigation math">
            <p>
              Pulsar&apos;s ~22.5 dB received-power advantage over GPS L1 C/A
              is documented in Xona&apos;s public{" "}
              <Ext href="https://www.xonaspace.com/">technology briefings</Ext>.
              From that:
            </p>
            <div className="mt-3 p-4 rounded-lg bg-bg-elevated font-mono-numbers text-xs leading-relaxed space-y-1">
              <div>power_ratio = 10^(22.5 / 10) ≈ 178x</div>
              <div>radius_ratio = sqrt(power_ratio) ≈ 13.3x</div>
              <div>practical reduction (free-space + receiver margin) ≈ 6.3x</div>
              <div>area_reduction = 1 − 1 / 6.3² ≈ 97.5%</div>
            </div>
            <p className="mt-3">
              Spoofing is modeled as fully eliminated because Pulsar implements{" "}
              <strong>cryptographic range authentication</strong> — a spoofer
              cannot forge a signed range measurement without the satellite key.
            </p>
          </Section>

          <Section title="4. Source code & API">
            <p>
              The full backend (FastAPI + PostgreSQL), the detection
              pipeline, the Pulsar modeler, and the frontend are MIT-licensed.
            </p>
            <ul className="list-disc pl-6 space-y-1.5 mt-2">
              <li>
                <Ext href={process.env.NEXT_PUBLIC_GITHUB_URL || "https://github.com/larrytzhang/xona"}>
                  GitHub repository
                </Ext>
              </li>
              <li>
                <Ext
                  href={
                    (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") +
                    "/docs"
                  }
                >
                  Interactive API documentation (Swagger)
                </Ext>
              </li>
              <li>
                <Link href="/pulsar" className="text-accent-cyan hover:underline">
                  Pulsar explainer (draggable simulator)
                </Link>
              </li>
            </ul>
          </Section>

          <Section title="5. Known limitations">
            <ul className="list-disc pl-6 space-y-1.5">
              <li>
                Synthetic demo data matches real-world distributions but does not
                replace operational data.
              </li>
              <li>
                Pulsar receiver availability and free-space path loss vary with
                geometry; 6.3x is a conservative planning number.
              </li>
              <li>
                ADS-B is only one of several inputs that real PNT resilience
                work would consider (INS, multi-constellation, terrestrial).
              </li>
            </ul>
          </Section>
        </div>
      </div>

      <Footer />
    </>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="glass rounded-xl p-6 md:p-8">
      <h2 className="text-xl font-semibold mb-3">{title}</h2>
      <div className="text-text-secondary text-sm leading-relaxed space-y-3">
        {children}
      </div>
    </section>
  );
}

function Ext({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-accent-cyan hover:underline inline-flex items-center gap-0.5"
    >
      {children}
      <ExternalLink size={11} className="inline-block" />
    </a>
  );
}

function Code({ children }: { children: React.ReactNode }) {
  return (
    <code className="font-mono-numbers text-[12px] px-1.5 py-0.5 rounded bg-bg-elevated border border-border-subtle text-text-primary">
      {children}
    </code>
  );
}
