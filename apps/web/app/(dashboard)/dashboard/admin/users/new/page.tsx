'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { UserCreateForm } from '@/features/user/components/UserForm';
import { useCreateUser } from '@/features/user/api/queries';
import { userCreateSchema, type UserCreateFormData } from '@/features/user/schemas';
import { ArrowLeft } from 'lucide-react';

export default function NewUserPage() {
  const router = useRouter();
  const createUser = useCreateUser();

  const handleSubmit = (data: UserCreateFormData) => {
    createUser.mutate(data, {
      onSuccess: () => {
        router.push('/dashboard/admin');
      },
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/dashboard/admin">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold">新建用户</h1>
          <p className="text-muted-foreground">
            创建一个新的用户账户
          </p>
        </div>
      </div>

      <div className="max-w-2xl">
        <UserCreateForm
          onSubmit={handleSubmit}
          isLoading={createUser.isPending}
        />
      </div>
    </div>
  );
}
