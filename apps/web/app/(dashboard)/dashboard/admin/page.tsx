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

export default function AdminPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">用户管理</h1>
          <p className="text-sm text-muted-foreground">管理系统中的所有用户</p>
        </div>
        <Button asChild>
          <Link href="/dashboard/admin/users/new">
            <Plus className="h-4 w-4" />
            创建用户
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader className="px-5 py-4">
          <CardTitle className="text-base">用户列表</CardTitle>
          <CardDescription>查看和管理系统用户</CardDescription>
        </CardHeader>
        <CardContent className="px-5 pb-5">
          <UserTable />
        </CardContent>
      </Card>
    </div>
  );
}