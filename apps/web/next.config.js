/** @type {import('next').NextConfig} */
const nextConfig = {
  // 启用 source map 以便调试
  productionBrowserSourceMaps: true,

  // 使用 Turbopack 配置（Next.js 16 默认）
  turbopack: {
    // Turbopack 配置选项
  },

  // 路由重定向
  async redirects() {
    return [
      {
        source: '/pm/tasks',
        destination: '/pm',
        permanent: true, // 301 永久重定向
      },
    ];
  },
};

export default nextConfig;
