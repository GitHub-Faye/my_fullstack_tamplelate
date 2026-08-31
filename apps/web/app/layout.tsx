// 导入 Next.js 的元数据类型定义
import type { Metadata } from "next";
// 导入 Google 字体（自托管，避免 layout shift）
import { Fira_Code, Fira_Sans } from "next/font/google";
// 导入全局样式表
import "./globals.css";
// 导入应用状态提供者组件
import { Providers } from "@/components/providers";
// 导入 Toast 通知组件
import { Toaster } from "@/components/ui/sonner";

// 正文字体：Fira Sans（管理后台优先使用，数字/拉丁清晰易读）
const firaSans = Fira_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-fira-sans",
  display: "swap",
});

// 等宽字体：Fira Code（scope 徽章、代码、ID 等）
const firaCode = Fira_Code({
  subsets: ["latin"],
  variable: "--font-fira-code",
  display: "swap",
});

// 定义页面元数据
export const metadata: Metadata = {
  title: {
    default: "MyApp · 全栈管理平台",
    template: "%s · MyApp",
  },
  description: "基于 FastAPI + Next.js 的全栈管理后台模板",
};

// 根布局组件 - 所有页面共享的布局结构
export default function RootLayout({
  children,  // 子组件（页面内容）
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      {/* 应用字体 CSS 变量到 body */}
      <body className={`${firaSans.variable} ${firaCode.variable}`}>
        {/* 包裹状态提供者 */}
        <Providers>
          {/* 渲染页面内容 */}
          {children}
          {/* Toast 通知组件 */}
          <Toaster />
        </Providers>
      </body>
    </html>
  );
}
