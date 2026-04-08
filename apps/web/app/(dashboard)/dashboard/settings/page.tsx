'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { useCurrentUser, useUpdateUserMe, useUpdatePassword } from '@/features/user/api/queries';
import { userUpdateMeSchema, updatePasswordSchema, type UserUpdateMeFormData, type UpdatePasswordFormData } from '@/features/user/schemas';
import { Loader2 } from 'lucide-react';

export default function SettingsPage() {
  const { data: user, isLoading } = useCurrentUser();
  const updateUserMe = useUpdateUserMe();
  const updatePassword = useUpdatePassword();

  const profileForm = useForm<UserUpdateMeFormData>({
    resolver: zodResolver(userUpdateMeSchema),
    defaultValues: {
      email: user?.email || '',
      full_name: user?.full_name || '',
    },
  });

  const passwordForm = useForm<UpdatePasswordFormData>({
    resolver: zodResolver(updatePasswordSchema),
    defaultValues: {
      current_password: '',
      new_password: '',
    },
  });

  // Update form values when user data loads
  if (user && !profileForm.formState.isDirty) {
    profileForm.setValue('email', user.email);
    profileForm.setValue('full_name', user.full_name || '');
  }

  const handleProfileSubmit = (data: UserUpdateMeFormData) => {
    updateUserMe.mutate(data);
  };

  const handlePasswordSubmit = (data: UpdatePasswordFormData) => {
    updatePassword.mutate(data, {
      onSuccess: () => {
        passwordForm.reset();
      },
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">设置</h1>
        <p className="text-muted-foreground">
          管理您的个人信息和账户安全
        </p>
      </div>

      <div className="grid gap-6 max-w-2xl">
        {/* Profile Settings */}
        <Card>
          <CardHeader>
            <CardTitle>个人信息</CardTitle>
          </CardHeader>
          <CardContent>
            <Form {...profileForm}>
              <form onSubmit={profileForm.handleSubmit(handleProfileSubmit)} className="space-y-4">
                <FormField
                  control={profileForm.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>邮箱</FormLabel>
                      <FormControl>
                        <Input type="email" {...field} value={field.value || ''} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={profileForm.control}
                  name="full_name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>姓名</FormLabel>
                      <FormControl>
                        <Input {...field} value={field.value || ''} placeholder="您的姓名" />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <Button type="submit" disabled={updateUserMe.isPending}>
                  {updateUserMe.isPending ? '保存中...' : '保存更改'}
                </Button>
              </form>
            </Form>
          </CardContent>
        </Card>

        {/* Password Settings */}
        <Card>
          <CardHeader>
            <CardTitle>修改密码</CardTitle>
          </CardHeader>
          <CardContent>
            <Form {...passwordForm}>
              <form onSubmit={passwordForm.handleSubmit(handlePasswordSubmit)} className="space-y-4">
                <FormField
                  control={passwordForm.control}
                  name="current_password"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>当前密码</FormLabel>
                      <FormControl>
                        <Input type="password" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={passwordForm.control}
                  name="new_password"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>新密码</FormLabel>
                      <FormControl>
                        <Input type="password" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <Button type="submit" disabled={updatePassword.isPending}>
                  {updatePassword.isPending ? '修改中...' : '修改密码'}
                </Button>
              </form>
            </Form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
