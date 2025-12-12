/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // Enable standalone output for Docker production builds
  output: 'standalone',
}

module.exports = nextConfig
