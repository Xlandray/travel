import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "images.unsplash.com",
        port: "",
        pathname: "/**",
        search: "",
      },
      {
        protocol: "https",
        hostname: "localhost",
        port: "8081",
        pathname: "/media/**",
        search: "",
      },
    ],
  },
};

export default nextConfig;
