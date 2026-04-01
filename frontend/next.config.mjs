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
          // Enforce HTTPS for 1 year (enable once deployed to HTTPS).
          // { key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains" },
          // Content Security Policy — restrict script/style/connect sources.
          {
            key: "Content-Security-Policy",
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-eval' 'unsafe-inline'",
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
              "font-src 'self' https://fonts.gstatic.com",
              "img-src 'self' data: blob:",
              "connect-src 'self' http://localhost:8000 https://*.neon.tech",
              "frame-ancestors 'none'",
            ].join("; "),
          },
        ],
      },
    ];
  },
};

export default nextConfig;
