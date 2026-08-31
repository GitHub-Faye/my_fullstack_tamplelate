"use client";

import Link from "next/link";
import { useCurrentUser, useUserScopes } from "@/features/user";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { ShieldCheck, Settings, Users, ArrowRight } from "lucide-react";
import { formatDate, formatUserRole, formatUserStatus } from "@/lib/utils";
import { hasScope, UserScope, RoleScope } from "@repo/contracts/scopes";

export default function DashboardPage() {
  const user = useCurrentUser();
  const scopes = useUserScopes();

  const quickActions = [
    {
      title: "用户管理",
      description: "查看与管理系统用户",
      href: "/dashboard/admin",
      icon: Users,
      show: hasScope(scopes, UserScope.READ),
    },
    {
      title: "角色管理",
      description: "管理角色与权限范围",
      href: "/dashboard/roles",
      icon: ShieldCheck,
      show: hasScope(scopes, RoleScope.READ),
    },
    {
      title: "个人设置",
      description: "更新资料与修改密码",
      href: "/dashboard/settings",
      icon: Settings,
      show: true,
    },
  ].filter((item) => item.show);

  const initials = (user?.full_name || user?.email || "U").slice(0, 2).toUpperCase();

  return (
    <div className="space-y-6">
      {/* 欢迎区 */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <Avatar className="h-14 w-14 border">
            <AvatarFallback className="text-base">{initials}</AvatarFallback>
          </Avatar>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              欢迎回来，{user?.full_name || user?.email}
            </h1>
            <p className="text-sm text-muted-foreground">
              这里是您的管理后台概览
            </p>
          </div>
        </div>
        <Badge variant={user?.is_superuser ? "default" : "secondary"} className="w-fit">
          {formatUserRole(user?.is_superuser)}
        </Badge>
      </div>

      {/* 快速操作 */}
      <section aria-label="快速操作">
        <h2 className="mb-3 text-sm font-semibold text-muted-foreground">
          快速操作
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <Button
                key={action.title}
                variant="outline"
                asChild
                className="card-hover h-auto justify-start gap-4 p-5"
              >
                <Link href={action.href}>
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <Icon className="h-5 w-5" />
                  </span>
                  <span className="flex flex-1 flex-col items-start gap-0.5">
                    <span className="text-sm font-semibold">{action.title}</span>
                    <span className="text-xs text-muted-foreground">
                      {action.description}
                    </span>
                  </span>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </Link>
              </Button>
            );
          })}
        </div>
      </section>

      {/* 账户信息 */}
      <section aria-label="账户信息">
        <h2 className="mb-3 text-sm font-semibold text-muted-foreground">
          账户信息
        </h2>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">基本信息</CardTitle>
            <CardDescription>您的账户基本信息与权限</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-x-8 gap-y-4 sm:grid-cols-2">
            <div className="flex justify-between gap-4">
              <span className="text-sm text-muted-foreground">邮箱</span>
              <span className="text-sm font-medium">{user?.email}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-sm text-muted-foreground">姓名</span>
              <span className="text-sm font-medium">{user?.full_name || "-"}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-sm text-muted-foreground">状态</span>
              <Badge variant={user?.is_active ? "default" : "destructive"}>
                {formatUserStatus(user?.is_active)}
              </Badge>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-sm text-muted-foreground">创建时间</span>
              <span className="text-sm font-medium">{formatDate(user?.created_at)}</span>
            </div>
            {scopes.length > 0 && (
              <div className="sm:col-span-2">
                <span className="text-sm text-muted-foreground">权限范围</span>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {scopes.map((scope) => (
                    <Badge key={scope} variant="outline" className="font-mono text-xs">
                      {scope}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
