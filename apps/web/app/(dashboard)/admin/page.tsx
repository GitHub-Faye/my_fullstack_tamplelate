'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Plus, Pencil, Trash2 } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  readUsersV1UsersUsersGet,
  deleteUserV1UsersUsersUserIdDelete,
} from '@repo/sdk';
import type { UserPublic } from '@repo/sdk';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { toast } from 'sonner';

export default function AdminPage() {
  const queryClient = useQueryClient();
  const [userToDelete, setUserToDelete] = useState<UserPublic | null>(null);

  const { data: usersData, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const response = await readUsersV1UsersUsersGet();
      return response.data;
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (userId: string) => {
      const response = await deleteUserV1UsersUsersUserIdDelete({
        path: { user_id: userId },
      });
      return response.data;
    },
    onSuccess: () => {
      toast.success('User deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setUserToDelete(null);
    },
    onError: (error) => {
      toast.error('Failed to delete user');
      console.error('Failed to delete user:', error);
    },
  });

  const handleDelete = (user: UserPublic) => {
    setUserToDelete(user);
  };

  const confirmDelete = () => {
    if (userToDelete) {
      deleteMutation.mutate(userToDelete.id);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  const users = usersData?.data || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">User Management</h1>
        <Button asChild>
          <Link href="/dashboard/admin/users/new">
            <Plus className="mr-2 h-4 w-4" /> Create New User
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Users</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground">
                    No users found
                  </TableCell>
                </TableRow>
              ) : (
                users.map((user: UserPublic) => (
                  <TableRow key={user.id}>
                    <TableCell className="font-medium">{user.full_name || '-'}</TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>
                      {user.is_superuser ? (
                        <span className="inline-flex items-center rounded-full bg-primary/10 px-2 py-1 text-xs font-medium text-primary">
                          Admin
                        </span>
                      ) : (
                        <span className="inline-flex items-center rounded-full bg-muted px-2 py-1 text-xs font-medium text-muted-foreground">
                          User
                        </span>
                      )}
                    </TableCell>
                    <TableCell>
                      {user.is_active ? (
                        <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-1 text-xs font-medium text-green-700">
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center rounded-full bg-red-100 px-2 py-1 text-xs font-medium text-red-700">
                          Inactive
                        </span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end space-x-2">
                        <Button variant="outline" size="sm" asChild>
                          <Link href={`/dashboard/admin/users/${user.id}/edit`}>
                            <Pencil className="h-4 w-4" />
                          </Link>
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDelete(user)}
                          disabled={deleteMutation.isPending}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!userToDelete} onOpenChange={() => setUserToDelete(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete User</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete {userToDelete?.full_name || userToDelete?.email}? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setUserToDelete(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={confirmDelete}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
