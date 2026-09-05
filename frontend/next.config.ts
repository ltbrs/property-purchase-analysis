import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async redirects() {
    return [
      {
        source: "/:path*",
        has: [{ type: "host", value: "www.acquora.fr" }],
        destination: "https://acquora.fr/:path*",
        permanent: true,
      },
    ];
  },
  turbopack: {
    root: process.cwd(),
  },
};

export default nextConfig;
