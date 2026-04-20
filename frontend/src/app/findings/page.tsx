"use client";

import { FindingCard, TrendChart, RegionChart } from "@/components/findings";
import { Footer } from "@/components/ui";
import { useFindings, useRegions, useStats } from "@/lib/hooks";

/**
 * Key Findings page — data-driven insights from the GPS interference analysis.
 *
 * Fetches pre-computed findings and per-region breakdowns from the backend
 * API. Displays 5 headline findings with animated cards, a trend chart
 * showing events over time by region, and a region comparison bar chart.
 *
 * Includes loading skeletons, error state with retry, and empty state
 * when findings have not yet been computed.
 */
export default function FindingsPage() {
  const findingsQuery = useFindings();
  const regionsQuery = useRegions();
  const statsQuery = useStats();

  const findings = findingsQuery.data?.findings ?? [];
  const regions = regionsQuery.data?.regions ?? [];
  const dateRange = statsQuery.data?.date_range;

  const isLoading = findingsQuery.isLoading || regionsQuery.isLoading || statsQuery.isLoading;
  const isError = findingsQuery.isError || regionsQuery.isError || statsQuery.isError;

  /** Retry failed queries. */
  const handleRetry = () => {
    findingsQuery.refetch();
    regionsQuery.refetch();
    statsQuery.refetch();
  };

  return (
    <>
      <div className="min-h-screen pt-20 pb-8 px-6 max-w-5xl mx-auto">
      {/* Hero */}
      <div className="mb-10">
        <h1 className="text-3xl md:text-4xl font-bold mb-2 tracking-tight">Key Findings</h1>
        <p className="text-text-secondary leading-relaxed max-w-2xl">
          Analysis of GPS interference events detected across 7 global conflict zones
          {dateRange ? `, ${new Date(dateRange.start).toLocaleDateString("en-US", { month: "long", year: "numeric" })} — ${new Date(dateRange.end).toLocaleDateString("en-US", { month: "long", year: "numeric" })}` : ""}.
          Synthetic ADS-B data modeling real-world interference patterns — see{" "}
          <a href="/methodology" className="text-accent-cyan hover:underline">methodology</a>.
        </p>
      </div>

      {/* Error state */}
      {isError && (
        <div className="glass rounded-xl p-6 max-w-md mx-auto text-center mb-10">
          <p className="text-text-primary font-medium mb-2">Could not load findings</p>
          <p className="text-text-muted text-sm mb-4">
            The backend API may be unavailable. Check that the server is running.
          </p>
          <button
            onClick={handleRetry}
            className="px-4 py-2 rounded-lg bg-accent-cyan/20 text-accent-cyan text-sm font-medium hover:bg-accent-cyan/30 transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading skeletons */}
      {isLoading && !isError && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-10">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="glass rounded-xl p-5 animate-pulse">
                <div className="h-3 bg-bg-elevated rounded w-3/4 mb-3" />
                <div className="h-8 bg-bg-elevated rounded w-1/2 mb-2" />
                <div className="h-3 bg-bg-elevated rounded w-full" />
              </div>
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="glass rounded-xl p-5 h-64 animate-pulse" />
            <div className="glass rounded-xl p-5 h-64 animate-pulse" />
          </div>
        </>
      )}

      {/* Empty state */}
      {!isLoading && !isError && findings.length === 0 && (
        <div className="glass rounded-xl p-6 max-w-md mx-auto text-center mb-10">
          <p className="text-text-primary font-medium mb-1">No findings computed yet</p>
          <p className="text-text-muted text-sm">
            Run the compute_findings script on the backend to generate analysis results.
          </p>
        </div>
      )}

      {/* Finding cards */}
      {findings.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-10">
          {findings.map((finding, i) => (
            <FindingCard key={finding.finding_key} finding={finding} index={i} />
          ))}
        </div>
      )}

      {/* Charts */}
      {regions.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <TrendChart regions={regions} />
          <RegionChart regions={regions} />
        </div>
      )}
      </div>
      <Footer />
    </>
  );
}
