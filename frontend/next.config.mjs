/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    optimizePackageImports: ["lucide-react", "recharts"],
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**",
      },
    ],
  },
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `http://localhost:8000/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
