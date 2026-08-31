import { notFound } from "next/navigation";
import { getRoleById } from "../api/server/queries";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/utils";
import Link from "next/link";
import { ArrowLeft, Shield } from "lucide-react";
import { BUILTIN_ROLES } from "@repo/contracts/scopes";

interface RoleDetailProps {
  roleId: string;
}

/**
 * RoleDetail Server Component
 * Fetches and displays a single role's details
 */
export async function RoleDetail({ roleId }: RoleDetailProps) {
  const role = await getRoleById(roleId);

  if (!role) {
    notFound();
  }

  const isBuiltin = (BUILTIN_ROLES as readonly string[]).includes(role.name);
  const scopes = role.scopes ?? [];

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

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Shield className="h-6 w-6 text-muted-foreground" />
            <div>
              <CardTitle className="flex items-center gap-2">
                {role.name}
                {isBuiltin && <Badge variant="secondary">预置</Badge>}
              </CardTitle>
              <CardDescription>角色详情</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4">
            <div className="flex flex-col gap-1">
              <span className="text-sm text-muted-foreground">权限 Scope</span>
              {scopes.length === 0 ? (
                <span className="text-sm">暂无权限</span>
              ) : (
                <div className="flex flex-wrap gap-1">
                  {scopes.map((scope) => (
                    <Badge key={scope} variant="outline" className="font-mono text-xs">
                      {scope}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-sm text-muted-foreground">创建时间</span>
              <span className="text-sm">{formatDate(role.created_at)}</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-sm text-muted-foreground">角色 ID</span>
              <span className="text-sm font-mono text-xs">{role.id}</span>
            </div>
          </div>

          {!isBuiltin && (
            <div className="flex gap-2 pt-4">
              <Button asChild>
                <Link href={`/dashboard/roles/${role.id}/edit`}>编辑角色</Link>
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
