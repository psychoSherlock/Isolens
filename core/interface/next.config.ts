import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    optimizePackageImports: ["react-icons"],
    proxyTimeout: 300_000, // 5 minutes in milliseconds to keep sandbox analysis & AI requests open
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:6969/api/:path*",
      },
    ];
  },
};

export default nextConfig;
