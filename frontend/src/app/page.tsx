/**
 * GPS Shield — Main Globe Page.
 *
 * The hero view of the app: a full-screen interactive 3D globe
 * displaying interference zones, with the Pulsar Mode toggle,
 * stats bar, region sidebar, and zone detail panel.
 *
 * Globe component will be added in Steps 17-19.
 * Dashboard panels will be added in Steps 20-22.
 */
export default function Home() {
  return (
    <div className="relative w-full h-screen pt-14 overflow-hidden">
      {/* Globe placeholder — will be replaced with deck.gl in Step 17 */}
      <div className="absolute inset-0 pt-14 flex items-center justify-center">
        <div className="text-center">
          <div className="w-32 h-32 mx-auto rounded-full bg-gradient-to-br from-accent-cyan/20 to-accent-cyan/5 flex items-center justify-center mb-6">
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-accent-cyan/30 to-transparent border border-accent-cyan/20" />
          </div>
          <h1 className="text-2xl font-semibold mb-2">GPS Shield</h1>
          <p className="text-text-secondary text-sm max-w-md">
            Analyzing millions of flight records to map the GPS spoofing crisis
            and model how Xona&apos;s Pulsar constellation would solve it.
          </p>
        </div>
      </div>
    </div>
  );
}
