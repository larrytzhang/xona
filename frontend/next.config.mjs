const isDev = process.env.NODE_ENV !== "production";

// Derive the backend origin from NEXT_PUBLIC_API_URL so the CSP connect-src
// allows the deployed API host. Falls back to localhost for local dev.
const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
let apiOrigin = "http://localhost:8000";
try {
  apiOrigin = new URL(apiUrl).origin;
} catch {
  apiOrigin = apiUrl;
}

// connect-src entries: self, the API origin, Neon (DB error responses proxied
// through backend never hit the browser, but keep the allowance for safety).
const connectSrc = [
  "'self'",
  apiOrigin,
  "https://*.neon.tech",
].join(" ");

/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ["@deck.gl/core", "@deck.gl/react", "@deck.gl/layers", "@deck.gl/geo-layers", "@luma.gl/core", "@luma.gl/webgl"],

  // Disable source maps in production to prevent code exposure.
  productionBrowserSourceMaps: false,

  // Security headers applied to all routes.
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          // Prevent clickjacking — do not allow embedding in iframes.
          { key: "X-Frame-Options", value: "DENY" },
          // Prevent MIME-type sniffing.
          { key: "X-Content-Type-Options", value: "nosniff" },
          // Control referrer information sent with requests.
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          // Restrict powerful browser APIs we do not use.
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
          },
          // Enforce HTTPS for 1 year in production only (prevents dev lockout).
          ...(isDev
            ? []
            : [{ key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains" }]),
          // Content Security Policy — restrict script/style/connect sources.
          {
            key: "Content-Security-Policy",
            value: [
              "default-src 'self'",
              `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""}`,
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
              "font-src 'self' https://fonts.gstatic.com",
              "img-src 'self' data: blob:",
              `connect-src ${connectSrc}`,
              "frame-ancestors 'none'",
              "base-uri 'self'",
              "form-action 'self'",
            ].join("; "),
          },
        ],
      },
    ];
  },
};

export default nextConfig;
