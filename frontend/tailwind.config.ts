import type { Config } from "tailwindcss";

/**
 * Tailwind CSS configuration for GPS Shield.
 *
 * Custom color tokens for the dark theme design system,
 * inspired by Xona Space Systems' branding (cyan accent).
 */
const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        "bg-primary": "#09090B",
        "bg-surface": "#111114",
        "bg-elevated": "#18181B",
        "accent-cyan": "#06B6D4",
        "accent-cyan-dim": "#0891B2",
        "severity-low": "#22C55E",
        "severity-moderate": "#EAB308",
        "severity-high": "#F97316",
        "severity-critical": "#EF4444",
        "text-primary": "#FAFAFA",
        "text-secondary": "#A1A1AA",
        "text-muted": "#71717A",
        "border-subtle": "#27272A",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      backdropBlur: {
        glass: "16px",
      },
    },
  },
  plugins: [],
};
export default config;
