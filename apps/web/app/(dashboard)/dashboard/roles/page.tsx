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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">角色管理</h1>
          <p className="text-muted-foreground">管理所有角色及其权限范围</p>
        </div>
        <Button asChild>
          <Link href="/dashboard/roles/new">
            <Plus className="mr-2 h-4 w-4" />
            新建角色
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>角色列表</CardTitle>
          <CardDescription>查看和管理角色（系统预置角色不可修改/删除）</CardDescription>
        </CardHeader>
        <CardContent>
          <RoleTable />
        </CardContent>
      </Card>
    </div>
  );
}
