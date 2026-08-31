import type { ReactNode } from "react";

interface AuthCardShellProps {
  /** 图标（lucide 组件） */
  icon: ReactNode;
  /** 卡片标题 */
  title: string;
  /** 卡片副标题 */
  description: string;
  children: ReactNode;
}

/**
 * 认证页卡片外壳
 * 统一 icon 徽章 + 标题 + 描述 + 内容的结构，保证三个 auth 页视觉一致
 */
export function AuthCardShell({ icon, title, description, children }: AuthCardShellProps) {
  return (
    <div className="glass rounded-2xl border shadow-lg">
      <div className="space-y-2 p-6 pb-2 text-center sm:p-8 sm:pb-2">
        <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
          {icon}
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          {title}
        </h1>
        <p className="mx-auto max-w-xs text-sm text-muted-foreground">
          {description}
        </p>
      </div>
      <div className="p-6 pt-4 sm:p-8 sm:pt-4">{children}</div>
    </div>
  );
}
