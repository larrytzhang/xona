/**
 * GPS Shield — Component smoke tests.
 *
 * Verifies that core UI components render without crashing and
 * expose the expected content and interactions.
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";

/* ------------------------------------------------------------------ */
/*  Mocks                                                              */
/* ------------------------------------------------------------------ */

// Mock next/link — render as a plain <a> tag
jest.mock("next/link", () => {
  return function MockLink({
    children,
    href,
    ...rest
  }: {
    children: React.ReactNode;
    href: string;
    [key: string]: unknown;
  }) {
    return (
      <a href={href} {...rest}>
        {children}
      </a>
    );
  };
});

// Mock next/navigation — provide a stub usePathname
jest.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

// Mock lucide-react icons — render as simple spans with the icon name
jest.mock("lucide-react", () => ({
  Globe: (props: Record<string, unknown>) => (
    <span data-testid="icon-globe" {...props} />
  ),
  BarChart3: (props: Record<string, unknown>) => (
    <span data-testid="icon-barchart3" {...props} />
  ),
  Shield: (props: Record<string, unknown>) => (
    <span data-testid="icon-shield" {...props} />
  ),
}));

// Mock the LivePulse component since StatsBar imports it
jest.mock("@/components/globe", () => ({
  LivePulse: (props: Record<string, unknown>) => (
    <div data-testid="live-pulse">{String(props.status ?? "inactive")}</div>
  ),
}));

/* ------------------------------------------------------------------ */
/*  Imports (after mocks)                                              */
/* ------------------------------------------------------------------ */

import { PulsarToggle } from "@/components/globe/PulsarToggle";
import { Nav } from "@/components/ui/Nav";
import { StatsBar } from "@/components/dashboard/StatsBar";
import type { StatsResponse } from "@/lib/types";

/* ------------------------------------------------------------------ */
/*  Test data                                                          */
/* ------------------------------------------------------------------ */

const mockStats: StatsResponse = {
  total_events: 1234,
  total_zones: 42,
  total_aircraft_affected: 567,
  date_range: { start: "2024-01-01", end: "2024-06-30" },
  by_type: { spoofing: 800, jamming: 300, mixed: 134 },
  avg_severity: 6.2,
  live: {
    active_zones: 5,
    events_last_hour: 12,
    last_poll: "2024-06-30T12:00:00Z",
    poll_status: "active",
  },
};

/* ================================================================== */
/*  PulsarToggle                                                       */
/* ================================================================== */

describe("PulsarToggle", () => {
  it("renders without crashing", () => {
    render(<PulsarToggle active={false} onToggle={() => {}} />);
  });

  it('shows "GPS Mode" text when active=false', () => {
    render(<PulsarToggle active={false} onToggle={() => {}} />);
    expect(screen.getByText("GPS Mode")).toBeInTheDocument();
  });

  it('shows "Pulsar Mode" text when active=true', () => {
    render(<PulsarToggle active={true} onToggle={() => {}} />);
    expect(screen.getByText("Pulsar Mode")).toBeInTheDocument();
  });

  it("calls onToggle when clicked", () => {
    const handleToggle = jest.fn();
    render(<PulsarToggle active={false} onToggle={handleToggle} />);
    fireEvent.click(screen.getByRole("switch"));
    expect(handleToggle).toHaveBeenCalledTimes(1);
  });

  it("has correct aria attributes", () => {
    const { rerender } = render(
      <PulsarToggle active={false} onToggle={() => {}} />
    );
    const toggle = screen.getByRole("switch");
    expect(toggle).toHaveAttribute("aria-checked", "false");
    expect(toggle).toHaveAttribute("aria-label", "Toggle Pulsar Mode");

    rerender(<PulsarToggle active={true} onToggle={() => {}} />);
    expect(screen.getByRole("switch")).toHaveAttribute("aria-checked", "true");
  });
});

/* ================================================================== */
/*  Nav                                                                */
/* ================================================================== */

describe("Nav", () => {
  it("renders GPS Shield logo/title", () => {
    render(<Nav />);
    expect(screen.getByText("GPS SHIELD")).toBeInTheDocument();
  });

  it("has links to /findings and /pulsar", () => {
    render(<Nav />);

    const findingsLink = screen.getByText("Findings").closest("a");
    expect(findingsLink).toHaveAttribute("href", "/findings");

    const pulsarLink = screen.getByText("How Pulsar Works").closest("a");
    expect(pulsarLink).toHaveAttribute("href", "/pulsar");
  });
});

/* ================================================================== */
/*  StatsBar                                                           */
/* ================================================================== */

describe("StatsBar", () => {
  it("renders without crashing when given mock data", () => {
    render(<StatsBar stats={mockStats} />);
  });

  it("shows loading text when stats is null", () => {
    render(<StatsBar stats={null} />);
    expect(screen.getByText("Loading statistics...")).toBeInTheDocument();
  });

  it("displays stat labels", () => {
    render(<StatsBar stats={mockStats} />);
    expect(screen.getByText("Events Detected")).toBeInTheDocument();
    expect(screen.getByText("Active Zones")).toBeInTheDocument();
    expect(screen.getByText("Aircraft Affected")).toBeInTheDocument();
    expect(screen.getByText("Analysis Period")).toBeInTheDocument();
  });
});
