'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Skeleton } from '@/components/ui/skeleton';
import { MoreHorizontal, Pencil, Trash2, User } from 'lucide-react';
import type { UserPublic } from '@repo/sdk';

interface UserTableProps {
  users: UserPublic[];
  isLoading?: boolean;
  onDelete?: (userId: string) => void;
  currentUserId?: string;
}

export function UserTable({ users, isLoading, onDelete, currentUserId }: UserTableProps) {
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [userToDelete, setUserToDelete] = useState<UserPublic | null>(null);

  const handleDeleteClick = (user: UserPublic) => {
    setUserToDelete(user);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = () => {
    if (userToDelete && onDelete) {
      onDelete(userToDelete.id);
    }
    setDeleteDialogOpen(false);
    setUserToDelete(null);
  };

  if (isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
      </div>
    );
  }

  return (
    <>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>用户</TableHead>
              <TableHead>邮箱</TableHead>
              <TableHead>状态</TableHead>
              <TableHead>角色</TableHead>
              <TableHead>创建时间</TableHead>
              <TableHead className="w-[50px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                  暂无用户数据
                </TableCell>
              </TableRow>
            ) : (
              users.map((user) => (
                <TableRow key={user.id}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <Avatar className="h-8 w-8">
                        <AvatarFallback>
                          {user.full_name?.charAt(0) || user.email.charAt(0).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <span className="font-medium">
                        {user.full_name || '未设置姓名'}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>{user.email}</TableCell>
                  <TableCell>
                    <Badge variant={user.is_active ? 'default' : 'secondary'}>
                      {user.is_active ? '激活' : '禁用'}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {user.is_superuser ? (
                      <Badge variant="destructive">超级管理员</Badge>
                    ) : (
                      <Badge variant="outline">普通用户</Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    {user.created_at
                      ? new Date(user.created_at).toLocaleDateString('zh-CN')
                      : '-'}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem asChild>
                          <Link href={`/dashboard/admin/users/${user.id}/edit`}>
                            <Pencil className="mr-2 h-4 w-4" />
                            编辑
                          </Link>
                        </DropdownMenuItem>
                        {user.id !== currentUserId && (
                          <DropdownMenuItem
                            className="text-destructive"
                            onClick={() => handleDeleteClick(user)}
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            删除
                          </DropdownMenuItem>
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

      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>
              您确定要删除用户 "{userToDelete?.full_name || userToDelete?.email}" 吗？此操作不可撤销。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              取消
            </Button>
            <Button variant="destructive" onClick={handleConfirmDelete}>
              删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
