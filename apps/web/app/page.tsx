"use client"; // 声明这是客户端组件（Next.js 13+ App Router 必须）

import { useEffect } from "react";
import { useRouter } from "next/navigation"; // 路由跳转钩子
import { useIsAuthenticated, useIsHydrated } from "@/src/stores/auth"; // 认证状态全局状态
import { Loader2 } from "lucide-react"; // 加载图标

export default function Home() {
  const router = useRouter(); // 获取路由实例，用于页面跳转
  const isAuthenticated = useIsAuthenticated(); // 获取用户是否已登录
  const isHydrated = useIsHydrated(); // 获取状态是否已完成初始化（水合完成）

  // 监听状态变化，执行自动跳转
  useEffect(() => {
    // 必须等状态水合完成后再判断，避免服务端/客户端状态不一致
    if (isHydrated) {
      // 如果用户已登录 → 跳转到仪表盘
      if (isAuthenticated) {
        router.replace("/dashboard");
      } 
      // 如果用户未登录 → 跳转到登录页
      else {
        router.replace("/login");
      }
    }
  }, [isHydrated, isAuthenticated, router]); // 依赖项：状态变化时重新执行

  // 跳转期间显示加载动画
  return (
    <div className="min-h-screen flex items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin" /> {/* 旋转加载图标 */}
    </div>
  );
}