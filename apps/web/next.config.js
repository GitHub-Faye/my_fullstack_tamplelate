/** @type {import('next').NextConfig} */
const nextConfig = {
  // 启用 source map 以便调试
  productionBrowserSourceMaps: true,
  
  // 使用 Turbopack 配置（Next.js 16 默认）
  turbopack: {
    // Turbopack 配置选项
  },
};

export default nextConfig;
