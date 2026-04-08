'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useCurrentUser } from '@/features/user/api/queries';
import { User, Mail, Shield, Calendar } from 'lucide-react';

export default function DashboardPage() {
  const { data: user, isLoading } = useCurrentUser();

  if (isLoading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">概览</h1>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">加载中...</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">-</div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">概览</h1>
        <p className="text-muted-foreground">
          欢迎回来，{user?.full_name || user?.email}
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">邮箱</CardTitle>
            <Mail className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-sm font-medium truncate">{user?.email}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">姓名</CardTitle>
            <User className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-sm font-medium">{user?.full_name || '未设置'}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">角色</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-sm font-medium">
              {user?.is_superuser ? '超级管理员' : '普通用户'}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">账户状态</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-sm font-medium">
              {user?.is_active ? '已激活' : '已禁用'}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>快速操作</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-sm text-muted-foreground">
            您可以通过左侧导航栏访问以下功能：
          </p>
          <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
            <li>用户管理 - 管理系统中的所有用户（仅管理员）</li>
            <li>设置 - 修改个人信息和密码</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
