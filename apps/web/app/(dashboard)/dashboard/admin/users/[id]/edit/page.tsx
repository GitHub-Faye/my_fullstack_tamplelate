'use client';

import Link from 'next/link';
import { useRouter, useParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { UserUpdateForm } from '@/features/user/components/UserForm';
import { useUser, useUpdateUser } from '@/features/user/api/queries';
import { type UserUpdateFormData } from '@/features/user/schemas';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

export default function EditUserPage() {
  const router = useRouter();
  const params = useParams();
  const userId = params.id as string;

  const { data: user, isLoading } = useUser(userId);
  const updateUser = useUpdateUser();

  const handleSubmit = (data: UserUpdateFormData) => {
    // Filter out empty password
    const submitData = {
      ...data,
      password: data.password || undefined,
    };

    updateUser.mutate(
      { userId, data: submitData },
      {
        onSuccess: () => {
          router.push('/dashboard/admin');
        },
      }
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild>
            <Link href="/dashboard/admin">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <h1 className="text-2xl font-bold">用户不存在</h1>
        </div>
        <p className="text-muted-foreground">找不到该用户的信息</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/dashboard/admin">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold">编辑用户</h1>
          <p className="text-muted-foreground">
            修改用户 {user.email} 的信息
          </p>
        </div>
      </div>

      <div className="max-w-2xl">
        <UserUpdateForm
          user={user}
          onSubmit={handleSubmit}
          isLoading={updateUser.isPending}
        />
      </div>
    </div>
  );
}
