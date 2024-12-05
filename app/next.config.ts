import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
};

module.exports = {
  env: {
    API_URL: process.env.API_URL, // Pass it explicitly if needed
  },
};

export default nextConfig;
