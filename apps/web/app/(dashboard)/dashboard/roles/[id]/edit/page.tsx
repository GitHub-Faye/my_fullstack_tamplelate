"use client";

import { useParams } from "next/navigation";
import { RoleForm } from "@/features/role/client/RoleForm";
import { useRole } from "@/features/role/api/client/queries";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function EditRolePage() {
  const params = useParams();
  const roleId = params.id as string;
  const { data: role, isLoading } = useRole(roleId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!role) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="outline" size="sm" asChild>
            <Link href="/dashboard/roles">
              <ArrowLeft className="mr-2 h-4 w-4" />
              返回列表
            </Link>
          </Button>
        </div>
        <div className="text-center py-12">
          <h2 className="text-xl font-semibold">角色不存在</h2>
          <p className="text-muted-foreground">该角色可能已被删除或您没有访问权限</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="sm" asChild>
          <Link href="/dashboard/roles">
            <ArrowLeft className="mr-2 h-4 w-4" />
            返回列表
          </Link>
        </Button>
      </div>

      <div>
        <h1 className="text-3xl font-bold">编辑角色</h1>
        <p className="text-muted-foreground">修改角色名称和权限范围</p>
      </div>

      <RoleForm role={role} mode="edit" />
    </div>
  );
}
