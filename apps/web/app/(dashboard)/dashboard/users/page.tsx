import { Plus } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import { UserTable } from "@/features/user/client";

export const metadata = {
  title: "账号管理",
  description: "管理所有用户账号",
};

/**
 * 管理员账号管理页面
 *
 * 展示所有用户账号，支持创建、编辑、禁用等操作
 * 从 /dashboard/admin 迁移到 /dashboard/users
 */
export default function AdminUsersPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">账号管理</h1>
          <p className="text-muted-foreground">管理系统中的所有用户</p>
        </div>
        <Button asChild>
          <Link href="/dashboard/users/new">
            <Plus className="mr-2 h-4 w-4" />
            创建用户
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>用户列表</CardTitle>
          <CardDescription>查看和管理系统用户</CardDescription>
        </CardHeader>
        <CardContent>
          <UserTable />
        </CardContent>
      </Card>
    </div>
  );
}