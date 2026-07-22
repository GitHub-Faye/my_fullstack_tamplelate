"use client";

import { useState } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Loader2,
  RotateCcw,
  Plus,
  Pencil,
  Trash2,
  X,
} from "lucide-react";
import { formatDate } from "@/lib/utils";
import {
  useAdminRoles,
  useAdminCreateRole,
  useAdminUpdateRole,
  useAdminDeleteRole,
} from "@/features/role/api";
import type { RolePublic, RoleCreate, RoleUpdate } from "@repo/sdk";

/**
 * 可选的 scope 列表（实际可从后端 scopes.py 同步）
 */
const SCOPE_OPTIONS = [
  { value: "task:read", label: "任务：查看" },
  { value: "task:create", label: "任务：创建" },
  { value: "task:update", label: "任务：更新" },
  { value: "task:delete", label: "任务：删除" },
  { value: "task:admin", label: "任务：管理" },
  { value: "task:approve", label: "任务：审核" },
  { value: "task:convert", label: "任务：转换类型" },
  { value: "task:reassign", label: "任务：改派" },
  { value: "bid:create", label: "报价：提交" },
  { value: "bid:update", label: "报价：修改" },
  { value: "bid:read", label: "报价：查看" },
  { value: "report:read", label: "日报：查看" },
  { value: "report:create", label: "日报：填写" },
  { value: "report:admin", label: "日报：管理" },
  { value: "starpoint:read", label: "星点：查看" },
  { value: "starpoint:admin", label: "星点：管理" },
  { value: "salary:read", label: "工资：查看" },
  { value: "salary:admin", label: "工资：管理" },
  { value: "client-resource:read", label: "客资：查看" },
  { value: "client-resource:create", label: "客资：录入" },
  { value: "user:read", label: "用户：查看" },
  { value: "user:create", label: "用户：创建" },
  { value: "user:update", label: "用户：更新" },
  { value: "user:delete", label: "用户：删除" },
  { value: "user:admin", label: "用户：管理" },
  { value: "rule:admin", label: "规则：管理" },
  { value: "dashboard:admin", label: "仪表板：管理员" },
  { value: "dashboard:engineer", label: "仪表板：工程师" },
  { value: "dashboard:pm", label: "仪表板：PM" },
];

export default function AdminRolesPage() {
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const { data, isLoading } = useAdminRoles({ page, page_size: pageSize });
  const createMutation = useAdminCreateRole();
  const updateMutation = useAdminUpdateRole();
  const deleteMutation = useAdminDeleteRole();

  const roles = (data?.data || []) as RolePublic[];
  const totalCount = data?.count || 0;
  const totalPages = Math.ceil(totalCount / pageSize);

  // 新增角色弹窗
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [createName, setCreateName] = useState("");
  const [createScopes, setCreateScopes] = useState<string[]>([]);

  // 编辑权限弹窗
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editRole, setEditRole] = useState<RolePublic | null>(null);
  const [editName, setEditName] = useState("");
  const [editScopes, setEditScopes] = useState<string[]>([]);

  // 删除确认弹窗
  const [deleteRole, setDeleteRole] = useState<RolePublic | null>(null);

  function resetCreateForm() {
    setCreateName("");
    setCreateScopes([]);
  }

  function resetEditForm() {
    setEditRole(null);
    setEditName("");
    setEditScopes([]);
  }

  async function handleCreate() {
    if (!createName.trim()) return;
    const body: RoleCreate = { name: createName.trim(), scopes: createScopes };
    await createMutation.mutateAsync({ body, url: "/v1/admin/roles" });
    setCreateDialogOpen(false);
    resetCreateForm();
  }

  async function handleUpdate() {
    if (!editRole || !editName.trim()) return;
    const body: RoleUpdate = { name: editName.trim(), scopes: editScopes };
    await updateMutation.mutateAsync({
      body,
      path: { role_id: editRole.id },
      url: "/v1/admin/roles/{role_id}",
    });
    setEditDialogOpen(false);
    resetEditForm();
  }

  async function handleDelete() {
    if (!deleteRole) return;
    await deleteMutation.mutateAsync({
      path: { role_id: deleteRole.id },
      url: "/v1/admin/roles/{role_id}",
    });
    setDeleteRole(null);
  }

  function openEditDialog(role: RolePublic) {
    setEditRole(role);
    setEditName(role.name);
    setEditScopes(role.scopes || []);
    setEditDialogOpen(true);
  }

  function toggleCreateScope(scope: string) {
    setCreateScopes((prev) =>
      prev.includes(scope) ? prev.filter((s) => s !== scope) : [...prev, scope],
    );
  }

  function toggleEditScope(scope: string) {
    setEditScopes((prev) =>
      prev.includes(scope) ? prev.filter((s) => s !== scope) : [...prev, scope],
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">角色管理</h1>
          <p className="text-muted-foreground">管理系统中的角色和权限</p>
        </div>
        <Button
          variant="default"
          size="sm"
          onClick={() => {
            resetCreateForm();
            setCreateDialogOpen(true);
          }}
        >
          <Plus className="mr-1 h-4 w-4" />
          新增角色
        </Button>
      </div>

      {/* 角色列表 */}
      <Card>
        <CardHeader>
          <CardTitle>角色列表</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>角色名称</TableHead>
                  <TableHead>权限范围</TableHead>
                  <TableHead>创建时间</TableHead>
                  <TableHead className="w-[120px] text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {roles.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center h-32">
                      暂无角色数据
                    </TableCell>
                  </TableRow>
                ) : (
                  roles.map((role) => (
                    <TableRow key={role.id}>
                      <TableCell className="font-medium">
                        {role.name}
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {(role.scopes || []).length === 0 ? (
                            <span className="text-muted-foreground text-sm">-</span>
                          ) : (
                            (role.scopes || []).map((s) => (
                              <Badge key={s} variant="secondary" className="text-xs">
                                {s}
                              </Badge>
                            ))
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {role.created_at ? formatDate(role.created_at) : "-"}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => openEditDialog(role)}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setDeleteRole(role)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {/* 分页 */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
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
                  上一页
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                >
                  下一页
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 新增角色弹窗 */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>新增角色</DialogTitle>
            <DialogDescription>
              输入角色名称并选择权限范围，创建新的系统角色。
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">角色名称</label>
              <Input
                placeholder="输入角色名称"
                value={createName}
                onChange={(e) => setCreateName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">权限范围</label>
              <div className="max-h-48 overflow-y-auto border rounded-md p-3 space-y-1">
                {SCOPE_OPTIONS.map((opt) => (
                  <label
                    key={opt.value}
                    className="flex items-center gap-2 text-sm cursor-pointer hover:bg-muted px-2 py-1 rounded"
                  >
                    <input
                      type="checkbox"
                      checked={createScopes.includes(opt.value)}
                      onChange={() => toggleCreateScope(opt.value)}
                      className="h-4 w-4"
                    />
                    {opt.label}
                    <span className="text-muted-foreground text-xs ml-auto">
                      {opt.value}
                    </span>
                  </label>
                ))}
              </div>
              {createScopes.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {createScopes.map((s) => (
                    <Badge key={s} variant="secondary" className="text-xs gap-1">
                      {s}
                      <X
                        className="h-3 w-3 cursor-pointer"
                        onClick={() => toggleCreateScope(s)}
                      />
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => { setCreateDialogOpen(false); resetCreateForm(); }}
            >
              取消
            </Button>
            <Button
              onClick={handleCreate}
              disabled={createMutation.isPending || !createName.trim()}
            >
              {createMutation.isPending ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />创建中...</>
              ) : "创建"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 编辑权限弹窗 */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>编辑权限</DialogTitle>
            <DialogDescription>
              修改角色名称和权限范围。
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">角色名称</label>
              <Input
                placeholder="输入角色名称"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">权限范围</label>
              <div className="max-h-48 overflow-y-auto border rounded-md p-3 space-y-1">
                {SCOPE_OPTIONS.map((opt) => (
                  <label
                    key={opt.value}
                    className="flex items-center gap-2 text-sm cursor-pointer hover:bg-muted px-2 py-1 rounded"
                  >
                    <input
                      type="checkbox"
                      checked={editScopes.includes(opt.value)}
                      onChange={() => toggleEditScope(opt.value)}
                      className="h-4 w-4"
                    />
                    {opt.label}
                    <span className="text-muted-foreground text-xs ml-auto">
                      {opt.value}
                    </span>
                  </label>
                ))}
              </div>
              {editScopes.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {editScopes.map((s) => (
                    <Badge key={s} variant="secondary" className="text-xs gap-1">
                      {s}
                      <X
                        className="h-3 w-3 cursor-pointer"
                        onClick={() => toggleEditScope(s)}
                      />
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => { setEditDialogOpen(false); resetEditForm(); }}
            >
              取消
            </Button>
            <Button
              onClick={handleUpdate}
              disabled={updateMutation.isPending || !editName.trim()}
            >
              {updateMutation.isPending ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />保存中...</>
              ) : "保存"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 删除确认弹窗 */}
      <AlertDialog open={!!deleteRole} onOpenChange={() => setDeleteRole(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除</AlertDialogTitle>
            <AlertDialogDescription>
              此操作将永久删除角色 <strong>{deleteRole?.name}</strong>，包括其关联的权限范围。此操作无法撤销。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
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
    </div>
  );
}