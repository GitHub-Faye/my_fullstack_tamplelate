"use client";

import Link from "next/link";
import { ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";

interface BrandProps {
  /** 是否包裹链接（auth 页为纯展示，dashboard 跳转首页） */
  href?: string;
  className?: string;
  /** 文字尺寸：default 用于侧边栏，sm 用于移动端顶栏 */
  size?: "default" | "sm";
  /** 点击回调（如移动端导航后关闭抽屉） */
  onClick?: () => void;
}

/**
 * 品牌标识：图标 + 产品名
 * 全站统一使用，保证视觉一致性
 */
export function Brand({
  href = "/dashboard",
  className,
  size = "default",
  onClick,
}: BrandProps) {
  const inner = (
    <>
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
        <ShieldCheck className="h-5 w-5" />
      </span>
      <span
        className={cn(
          "font-bold tracking-tight text-foreground",
          size === "default" ? "text-base" : "text-sm"
        )}
      >
        MyApp
      </span>
    </>
  );

  return (
    <Link
      href={href}
      className={cn("flex items-center gap-2.5", className)}
      onClick={onClick}
      aria-label="MyApp 首页"
    >
      {inner}
    </Link>
  );
}
