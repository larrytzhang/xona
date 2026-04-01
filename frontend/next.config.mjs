/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ["@deck.gl/core", "@deck.gl/react", "@deck.gl/layers", "@deck.gl/geo-layers", "@luma.gl/core", "@luma.gl/webgl"],
};

export default nextConfig;
