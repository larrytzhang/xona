import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "GPS Shield — Mapping the GPS spoofing crisis";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

/**
 * Dynamic OpenGraph image generated at request time via next/og.
 * Used by link unfurlers (iMessage, Slack, Twitter, LinkedIn) when the
 * demo URL is pasted anywhere.
 */
export default async function OgImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          background: "linear-gradient(135deg, #09090B 0%, #111114 100%)",
          color: "#FAFAFA",
          fontFamily: "system-ui, sans-serif",
          padding: "80px",
          position: "relative",
        }}
      >
        <div
          style={{
            position: "absolute",
            right: "80px",
            top: "100px",
            width: "440px",
            height: "440px",
            borderRadius: "220px",
            background:
              "radial-gradient(circle at 35% 40%, rgba(34,211,238,0.5) 0%, rgba(6,182,212,0.25) 40%, rgba(14,116,144,0) 80%)",
          }}
        />
        <div
          style={{
            position: "absolute",
            right: "260px",
            top: "280px",
            width: "80px",
            height: "80px",
            borderRadius: "40px",
            background: "#06B6D4",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <div
            style={{
              width: "28px",
              height: "28px",
              borderRadius: "14px",
              background: "#09090B",
            }}
          />
        </div>

        <div style={{ display: "flex", flexDirection: "column", maxWidth: "680px" }}>
          <div
            style={{
              fontSize: "22px",
              color: "#06B6D4",
              letterSpacing: "4px",
              marginBottom: "32px",
              fontWeight: 500,
            }}
          >
            GPS SHIELD
          </div>
          <div
            style={{
              fontSize: "72px",
              fontWeight: 700,
              lineHeight: 1.05,
              marginBottom: "24px",
              letterSpacing: "-1.5px",
            }}
          >
            Mapping the GPS spoofing crisis.
          </div>
          <div style={{ fontSize: "26px", color: "#A1A1AA", lineHeight: 1.4, marginBottom: "40px" }}>
            Modeling how Xona Pulsar LEO navigation neutralizes GPS
            interference worldwide.
          </div>
          <div
            style={{
              display: "flex",
              padding: "14px 28px",
              background: "#06B6D4",
              color: "#09090B",
              borderRadius: "28px",
              fontSize: "18px",
              fontWeight: 600,
              width: "fit-content",
            }}
          >
            Toggle Pulsar Mode →
          </div>
          <div style={{ fontSize: "15px", color: "#71717A", marginTop: "28px" }}>
            97.5% area reduction · spoofing eliminated · ~178x signal advantage
          </div>
        </div>
      </div>
    ),
    { ...size }
  );
}
