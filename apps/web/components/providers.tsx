"use client";

// React Query 客户端组件 - 为应用提供数据获取和缓存功能
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
// React Query 开发者工具 - 用于调试和监控查询状态
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { useState, type ReactNode } from "react";

// 提供者组件属性接口
interface ProvidersProps {
  children: ReactNode; // 子组件
}

// 全局状态提供者组件
// 包装整个应用，提供 React Query 功能
export function Providers({ children }: ProvidersProps) {
  // 使用 useState 延迟创建 QueryClient 实例
  // 确保在服务端渲染时不会创建多个实例
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // 数据缓存有效期：1分钟（60秒 * 1000毫秒）
            staleTime: 60 * 1000,
            // 窗口重新获得焦点时不自动重新获取数据
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    // QueryClientProvider 为子组件提供 queryClient 上下文
    <QueryClientProvider client={queryClient}>
      {children}
      {/* React Query 开发者工具，仅在开发环境显示 */}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
