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
  RotateCcw,
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
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
import { Card, CardContent } from "@/components/ui/card";

import { useUsers, useDeleteUser, userKeys } from "../api/client/queries";
import { useAdminToggleUserActive, useAdminResetPassword } from "../api/client/admin-queries";
import { formatDateShort, ROLE_LABELS, EMPLOYMENT_STATUS_LABELS, EMPLOYMENT_STATUS_VARIANTS } from "@/lib/utils";
import { useQueryClient } from "@tanstack/react-query";
import { useUserMap } from "../api/client/queries";
import type { UserAdminDetail } from "@repo/sdk";

interface UserTableProps {
  currentUserId?: string;
}

export function UserTable({ currentUserId }: UserTableProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [userToDelete, setUserToDelete] = useState<string | null>(null);
  const [userToToggle, setUserToToggle] = useState<string | null>(null);
  const [toggleTargetActive, setToggleTargetActive] = useState(false);
  const [userToResetPwd, setUserToResetPwd] = useState<string | null>(null);
  const [resetPwdInput, setResetPwdInput] = useState("");
  const [departmentFilter, setDepartmentFilter] = useState("all");
  const pageSize = 10;

  const { data, isLoading } = useUsers({ page, page_size: pageSize });
  const deleteMutation = useDeleteUser();
  const toggleActiveMutation = useAdminToggleUserActive();
  const resetPwdMutation = useAdminResetPassword();

  const users = (data?.data || []) as UserAdminDetail[];
  const totalCount = data?.count || 0;
  const totalPages = Math.ceil(totalCount / pageSize);

  // 从全量用户映射中提取所有部门（跨页）
  const userMap = useUserMap();
  const allDepartments = [...new Set(
    (data?.data as UserAdminDetail[] || [])
      .map((u) => u.department)
      .filter(Boolean)
  )] as string[];

  // 当部门筛选且命中当前页时，仍用当前页数据
  const filteredUsers = departmentFilter === "all"
    ? users
    : users.filter((u) => u.department === departmentFilter);

  async function handleDelete(userId: string) {
    try {
      await deleteMutation.mutateAsync(userId);
      setUserToDelete(null);
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
    } catch {
      // Error is handled by the mutation
    }
  }

  async function handleToggleActive(userId: string, isActive: boolean) {
    try {
      await toggleActiveMutation.mutateAsync({
        path: { user_id: userId },
        body: { is_active: isActive },
        url: '/v1/admin/users/{user_id}/toggle-active',
      });
      setUserToToggle(null);
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
    } catch {
      // Error is handled by the mutation
    }
  }

  async function handleResetPassword(userId: string) {
    try {
      await resetPwdMutation.mutateAsync({
        path: { user_id: userId },
        body: { new_password: resetPwdInput },
        url: '/v1/admin/users/{user_id}/reset-password',
      });
      setUserToResetPwd(null);
      setResetPwdInput("");
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
      {/* 筛选栏 */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <label className="text-sm text-muted-foreground">部门</label>
              <Select value={departmentFilter} onValueChange={(v) => { setDepartmentFilter(v); setPage(1); }}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="全部部门" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部部门</SelectItem>
                  {allDepartments.map((dep) => (
                    <SelectItem key={dep} value={dep}>{dep}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button variant="ghost" size="sm" onClick={() => { setDepartmentFilter("all"); setPage(1); }}>
              <RotateCcw className="mr-1 h-4 w-4" />
              重置
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>姓名</TableHead>
              <TableHead>邮箱</TableHead>
              <TableHead>手机号</TableHead>
              <TableHead>角色</TableHead>
              <TableHead>部门</TableHead>
              <TableHead>入职日期</TableHead>
              <TableHead>在岗状态</TableHead>
              <TableHead>账号状态</TableHead>
              <TableHead className="w-[50px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredUsers.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} className="text-center h-32">
                  暂无用户数据
                </TableCell>
              </TableRow>
            ) : (
              filteredUsers.map((user) => (
                <TableRow key={user.id}>
                  <TableCell className="font-medium">{user.full_name || "-"}</TableCell>
                  <TableCell>{user.email}</TableCell>
                  <TableCell>{user.phone || "-"}</TableCell>
                  <TableCell>
                    <Badge variant="secondary">
                      {ROLE_LABELS[user.role] || user.role}
                    </Badge>
                  </TableCell>
                  <TableCell>{user.department || "-"}</TableCell>
                  <TableCell>{user.hire_date ? formatDateShort(user.hire_date) : "-"}</TableCell>
                  <TableCell>
                    {user.employment_status ? (
                      <Badge variant={EMPLOYMENT_STATUS_VARIANTS[user.employment_status] || "outline"}>
                        {EMPLOYMENT_STATUS_LABELS[user.employment_status] || user.employment_status}
                      </Badge>
                    ) : "-"}
                  </TableCell>
                  <TableCell>
                    <Badge variant={user.is_active ? "default" : "destructive"}>
                      {user.is_active ? "活跃" : "已禁用"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => router.push(`/admin/users/${user.id}/edit`)}
                        >
                          <Pencil className="mr-2 h-4 w-4" />
                          编辑
                        </DropdownMenuItem>
                        {user.id !== currentUserId && (
                          <>
                            <DropdownMenuItem
                              onClick={() => {
                                setUserToToggle(user.id);
                                setToggleTargetActive(!user.is_active);
                              }}
                            >
                              {user.is_active ? "禁用" : "启用"}
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => setUserToResetPwd(user.id)}
                            >
                              重置密码
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              className="text-destructive"
                              onClick={() => setUserToDelete(user.id)}
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              删除
                            </DropdownMenuItem>
                          </>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
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
      <AlertDialog open={!!userToDelete} onOpenChange={() => setUserToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除</AlertDialogTitle>
            <AlertDialogDescription>
              此操作将永久删除该用户账户，包括其所有相关数据。此操作无法撤销。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => userToDelete && handleDelete(userToDelete)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />删除中...</>
              ) : "删除"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Toggle Active Confirmation Dialog */}
      <AlertDialog open={!!userToToggle} onOpenChange={() => setUserToToggle(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{toggleTargetActive ? "启用用户" : "禁用用户"}</AlertDialogTitle>
            <AlertDialogDescription>
              {toggleTargetActive ? "确认启用此用户？启用后用户可以正常登录系统。" : "确认禁用此用户？禁用后用户将无法登录系统。"}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => userToToggle && handleToggleActive(userToToggle, toggleTargetActive)}
              disabled={toggleActiveMutation.isPending}
            >
              {toggleActiveMutation.isPending ? "处理中..." : "确认"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Reset Password Dialog */}
      <AlertDialog open={!!userToResetPwd} onOpenChange={() => { setUserToResetPwd(null); setResetPwdInput(""); }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>重置密码</AlertDialogTitle>
            <AlertDialogDescription>
              输入新密码为用户重置密码。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="py-4">
            <Input
              type="password"
              placeholder="至少8个字符"
              value={resetPwdInput}
              onChange={(e) => setResetPwdInput(e.target.value)}
              minLength={8}
            />
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => userToResetPwd && handleResetPassword(userToResetPwd)}
              disabled={resetPwdMutation.isPending || resetPwdInput.length < 8}
            >
              {resetPwdMutation.isPending ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />重置中...</>
              ) : "确认重置"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}