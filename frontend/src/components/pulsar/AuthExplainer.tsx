"use client";

import { Lock, Unlock, ShieldCheck, ShieldAlert } from "lucide-react";

/**
 * Visual explainer for Pulsar's cryptographic range authentication.
 *
 * Shows GPS (open lock, vulnerable) vs Pulsar (closed lock, authenticated)
 * with an explanation of why spoofing is impossible with crypto auth.
 *
 * @returns The authentication explainer section element.
 */
export function AuthExplainer() {
  return (
    <div className="glass rounded-xl p-8">
      <h2 className="text-2xl font-bold mb-2">Spoofing Immunity</h2>
      <p className="text-text-secondary mb-6">
        Pulsar is the first navigation system with cryptographic range
        authentication. A spoofer cannot forge the signal — period.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* GPS - Vulnerable */}
        <div className="p-5 rounded-xl bg-severity-critical/5 border border-severity-critical/20">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-severity-critical/20 flex items-center justify-center">
              <Unlock size={20} className="text-severity-critical" />
            </div>
            <div>
              <div className="font-semibold">GPS Signal</div>
              <div className="flex items-center gap-1.5">
                <ShieldAlert size={12} className="text-severity-critical" />
                <span className="text-xs text-severity-critical font-medium">VULNERABLE</span>
              </div>
            </div>
          </div>
          <p className="text-sm text-text-secondary">
            GPS civilian signals have no authentication. Any transmitter can
            broadcast a fake GPS signal, causing receivers to compute
            incorrect positions.
          </p>
        </div>

        {/* Pulsar - Authenticated */}
        <div className="p-5 rounded-xl bg-accent-cyan/5 border border-accent-cyan/20">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-accent-cyan/20 flex items-center justify-center">
              <Lock size={20} className="text-accent-cyan" />
            </div>
            <div>
              <div className="font-semibold">Pulsar Signal</div>
              <div className="flex items-center gap-1.5">
                <ShieldCheck size={12} className="text-severity-low" />
                <span className="text-xs text-severity-low font-medium">AUTHENTICATED</span>
              </div>
            </div>
          </div>
          <p className="text-sm text-text-secondary">
            Pulsar implements range authentication — cryptographic proof
            that the signal came from a real satellite at the correct distance.
            Spoofing is mathematically impossible.
          </p>
        </div>
      </div>

      <div className="p-3 rounded-lg bg-severity-low/10 border border-severity-low/20">
        <span className="text-sm text-severity-low font-medium">
          100% of spoofing events in our analysis would be eliminated by Pulsar&apos;s
          cryptographic authentication.
        </span>
      </div>
    </div>
  );
}
