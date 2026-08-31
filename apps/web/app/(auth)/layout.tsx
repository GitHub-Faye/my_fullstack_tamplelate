"use client";

import type { ReactNode } from "react";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useIsAuthenticated, useIsHydrated } from "@/features/user";
import { Loader2 } from "lucide-react";
import { Brand } from "@/components/brand";
import { ThemeToggle } from "@/components/theme-toggle";

export default function AuthLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const isAuthenticated = useIsAuthenticated();
  const isHydrated = useIsHydrated();

  useEffect(() => {
    // Redirect to dashboard if already authenticated
    if (isHydrated && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isHydrated, isAuthenticated, router]);

  // Show loading while store is hydrating
  if (!isHydrated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // If authenticated, show loading (will redirect)
  if (isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-background p-4 sm:p-6">
      {/* 背景装饰光晕 */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 overflow-hidden"
      >
        <div className="absolute -top-32 left-1/2 h-[28rem] w-[28rem] -translate-x-1/2 rounded-full bg-primary/10 blur-3xl" />
        <div className="absolute bottom-[-8rem] left-[10%] h-[20rem] w-[20rem] rounded-full bg-accent/20 blur-3xl" />
      </div>

      {/* 顶部品牌 + 主题切换 */}
      <header className="absolute inset-x-0 top-0 flex h-16 items-center justify-between px-4 sm:px-6">
        <Brand href="/login" />
        <ThemeToggle />
      </header>

      {/* 主内容区 */}
      <main className="relative z-10 w-full max-w-md">{children}</main>

      {/* 页脚版权 */}
      <footer className="absolute inset-x-0 bottom-0 pb-4 text-center text-xs text-muted-foreground">
        © {new Date().getFullYear()} MyApp · 全栈管理平台
      </footer>
    </div>
  );
}
