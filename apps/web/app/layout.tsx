// 导入 Next.js 的元数据类型定义
import type { Metadata } from "next";
// 导入本地字体加载器
import localFont from "next/font/local";
// 导入全局样式表
import "./globals.css";
// 导入应用状态提供者组件
import { Providers } from "@/components/providers";
// 导入 Toast 通知组件
import { Toaster } from "@/components/ui/sonner";

// 定义 Geist Sans 字体配置
const geistSans = localFont({
  src: "./fonts/GeistVF.woff",  // 字体文件路径
  variable: "--font-geist-sans", // CSS 变量名
});

// 定义 Geist Mono 等宽字体配置
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff", // 字体文件路径
  variable: "--font-geist-mono",   // CSS 变量名
});

// 定义页面元数据
export const metadata: Metadata = {
  title: "My App",                           // 页面标题
  description: "A full-stack application built with Next.js", // 页面描述
};

// 根布局组件 - 所有页面共享的布局结构
export default function RootLayout({
  children,  // 子组件（页面内容）
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      {/* 应用字体 CSS 变量到 body */}
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
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
