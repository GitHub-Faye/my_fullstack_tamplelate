'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { UserTable } from '@/features/user/components/UserTable';
import { useUsers, useDeleteUser, useCurrentUser } from '@/features/user/api/queries';
import { Plus, Users } from 'lucide-react';
import { useState } from 'react';

export default function AdminUsersPage() {
  const [skip] = useState(0);
  const [limit] = useState(100);
  
  const { data: usersData, isLoading } = useUsers(skip, limit);
  const { data: currentUser } = useCurrentUser();
  const deleteUser = useDeleteUser();

  const handleDelete = (userId: string) => {
    deleteUser.mutate(userId);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">用户管理</h1>
          <p className="text-muted-foreground">
            管理系统中的所有用户账户
          </p>
        </div>
        <Button asChild>
          <Link href="/dashboard/admin/users/new">
            <Plus className="mr-2 h-4 w-4" />
            新建用户
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            用户列表
            {usersData && (
              <span className="text-sm font-normal text-muted-foreground">
                (共 {usersData.count} 人)
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <UserTable
            users={usersData?.data || []}
            isLoading={isLoading}
            onDelete={handleDelete}
            currentUserId={currentUser?.id}
          />
        </CardContent>
      </Card>
    </div>
  );
}
