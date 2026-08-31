"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  MoreHorizontal,
  Pencil,
  Trash2,
  Loader2,
  ChevronLeft,
  ChevronRight,
  Shield,
  BadgeCheck,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

import { useRoles, useDeleteRole, roleKeys } from "../api/client/queries";
import { formatDate } from "@/lib/utils";
import { useQueryClient } from "@tanstack/react-query";
import { BUILTIN_ROLES } from "@repo/contracts/scopes";

export function RoleTable() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [roleToDelete, setRoleToDelete] = useState<string | null>(null);
  const pageSize = 10;

  const { data, isLoading } = useRoles({ page, page_size: pageSize });
  const deleteMutation = useDeleteRole();

  const roles = (data?.data as Array<{
    id: string;
    name: string;
    scopes?: string[];
    created_at?: string | null;
  }>) || [];
  const totalCount = data?.count || 0;
  const totalPages = Math.ceil(totalCount / pageSize);

  function isBuiltin(name: string) {
    return (BUILTIN_ROLES as readonly string[]).includes(name);
  }

  async function handleDelete(roleId: string) {
    try {
      await deleteMutation.mutateAsync(roleId);
      setRoleToDelete(null);
      // Refresh the list
      queryClient.invalidateQueries({ queryKey: roleKeys.lists() });
    } catch {
      // Error is handled by the mutation
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>角色名</TableHead>
              <TableHead>权限 Scope</TableHead>
              <TableHead>创建时间</TableHead>
              <TableHead className="w-[50px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {roles.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center h-32">
                  <div className="flex flex-col items-center justify-center text-muted-foreground">
                    <Shield className="h-8 w-8 mb-2" />
                    <p>暂无角色数据</p>
                    <p className="text-sm">点击上方按钮创建新角色</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              roles.map((role) => {
                const builtin = isBuiltin(role.name);
                return (
                  <TableRow key={role.id}>
                    <TableCell className="font-medium">
                      <span className="flex items-center gap-2">
                        {role.name}
                        {builtin && (
                          <Badge variant="secondary" className="gap-1">
                            <BadgeCheck className="h-3 w-3" />
                            预置
                          </Badge>
                        )}
                      </span>
                    </TableCell>
                    <TableCell className="max-w-xs">
                      <div className="flex flex-wrap gap-1">
                        {(role.scopes ?? []).length === 0 ? (
                          <span className="text-muted-foreground text-sm">-</span>
                        ) : (
                          (role.scopes ?? []).map((scope) => (
                            <Badge key={scope} variant="outline" className="font-mono text-xs">
                              {scope}
                            </Badge>
                          ))
                        )}
                      </div>
                    </TableCell>
                    <TableCell>{formatDate(role.created_at)}</TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            disabled={builtin}
                            onClick={() =>
                              router.push(`/dashboard/roles/${role.id}/edit`)
                            }
                          >
                            <Pencil className="mr-2 h-4 w-4" />
                            编辑
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            className="text-destructive"
                            disabled={builtin}
                            onClick={() => setRoleToDelete(role.id)}
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            删除
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            共 {totalCount} 条记录，第 {page} / {totalPages} 页
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <AlertDialog
        open={!!roleToDelete}
        onOpenChange={() => setRoleToDelete(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除</AlertDialogTitle>
            <AlertDialogDescription>
              此操作将永久删除该角色，引用此角色的用户会自动解除关联。此操作无法撤销。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => roleToDelete && handleDelete(roleToDelete)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  删除中...
                </>
              ) : (
                "删除"
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
