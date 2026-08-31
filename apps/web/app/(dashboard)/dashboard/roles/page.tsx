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

import { RoleTable } from "@/features/role/client";

export const metadata = {
  title: "角色管理",
  description: "管理角色与权限范围",
};

export default function RolesPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">角色管理</h1>
          <p className="text-sm text-muted-foreground">管理所有角色及其权限范围</p>
        </div>
        <Button asChild>
          <Link href="/dashboard/roles/new">
            <Plus className="h-4 w-4" />
            新建角色
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader className="px-5 py-4">
          <CardTitle className="text-base">角色列表</CardTitle>
          <CardDescription>查看和管理角色（系统预置角色不可修改/删除）</CardDescription>
        </CardHeader>
        <CardContent className="px-5 pb-5">
          <RoleTable />
        </CardContent>
      </Card>
    </div>
  );
}