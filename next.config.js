/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for better deployment
  output: 'standalone',
  
  // Disable eslint during builds (optional)
  eslint: {
    ignoreDuringBuilds: true
  },
  
  // Handle images
  images: {
    unoptimized: true
  },
  
  // Environment variables that should be available on the client side
  env: {
    CUSTOM_KEY: 'my-value',
  }
}

module.exports = nextConfig