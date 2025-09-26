import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  reactStrictMode: true,
  images: {
    domains: ['yts.mx', 'image.tmdb.org'],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'ujbctboiqjsoskaflslz.supabase.co',
        pathname: '/storage/v1/object/public/**',
      },
    ],
  },
};

export default nextConfig;
