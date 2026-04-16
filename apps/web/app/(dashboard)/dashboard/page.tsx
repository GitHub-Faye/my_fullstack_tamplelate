"use client";

import { useCurrentUser } from "@/features/user";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatUserRole, formatUserStatus, formatDate } from "@/src/lib/utils";

export default function DashboardPage() {
  const user = useCurrentUser();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">仪表盘</h1>
        <p className="text-muted-foreground">
          欢迎回来，{user?.full_name || user?.email}
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>账户信息</CardTitle>
            <CardDescription>您的账户基本信息</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">邮箱</span>
              <span>{user?.email}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">姓名</span>
              <span>{user?.full_name || "-"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">角色</span>
              <Badge variant={user?.is_superuser ? "default" : "secondary"}>
                {formatUserRole(user?.is_superuser)}
              </Badge>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">状态</span>
              <Badge variant={user?.is_active ? "default" : "destructive"}>
                {formatUserStatus(user?.is_active)}
              </Badge>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">创建时间</span>
              <span>{formatDate(user?.created_at)}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>快速操作</CardTitle>
            <CardDescription>常用功能入口</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <p className="text-sm text-muted-foreground">
              您可以通过左侧导航栏访问更多功能。
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
