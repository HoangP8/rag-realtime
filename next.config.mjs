/** @type {import('next').NextConfig} */
const nextConfig = {
  // Re-enable linting and type checking for better development experience
  eslint: {
    ignoreDuringBuilds: false,
  },
  typescript: {
    ignoreBuildErrors: false,
  },
  // Enable image optimization for better performance
  images: {
    unoptimized: false,
    domains: [], // Add your image domains here if needed
  },
  // Performance optimizations
  experimental: {
    optimizeCss: true,
    optimizePackageImports: ['@radix-ui/react-icons', 'lucide-react'],
  },
  // Conditionally include webpack config only when not using Turbopack
  ...(process.env.TURBOPACK ? {} : {
    // Webpack optimizations
    webpack: (config, { dev, isServer }) => {
      if (!dev && !isServer) {
        config.optimization.splitChunks.chunks = 'all';
      }
      return config;
    },
  }),
}

export default nextConfig
