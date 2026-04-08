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
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { userCreateSchema, userUpdateSchema, type UserCreateFormData, type UserUpdateFormData } from '../schemas';
import type { UserPublic } from '@repo/sdk';

interface UserCreateFormProps {
  onSubmit: (data: UserCreateFormData) => void;
  isLoading?: boolean;
}

interface UserUpdateFormProps {
  user: UserPublic;
  onSubmit: (data: UserUpdateFormData) => void;
  isLoading?: boolean;
}

export function UserCreateForm({ onSubmit, isLoading }: UserCreateFormProps) {
  const form = useForm<UserCreateFormData>({
    resolver: zodResolver(userCreateSchema),
    defaultValues: {
      email: '',
      password: '',
      full_name: '',
      is_active: true,
      is_superuser: false,
    },
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>创建新用户</CardTitle>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>邮箱</FormLabel>
                  <FormControl>
                    <Input type="email" placeholder="user@example.com" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>密码</FormLabel>
                  <FormControl>
                    <Input type="password" placeholder="至少8个字符" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="full_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>姓名</FormLabel>
                  <FormControl>
                    <Input placeholder="用户姓名（可选）" {...field} value={field.value || ''} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="flex gap-4">
              <FormField
                control={form.control}
                name="is_active"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                    <div className="space-y-1 leading-none">
                      <FormLabel>激活用户</FormLabel>
                    </div>
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="is_superuser"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                    <div className="space-y-1 leading-none">
                      <FormLabel>超级管理员</FormLabel>
                    </div>
                  </FormItem>
                )}
              />
            </div>
            <Button type="submit" disabled={isLoading} className="w-full">
              {isLoading ? '创建中...' : '创建用户'}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}

export function UserUpdateForm({ user, onSubmit, isLoading }: UserUpdateFormProps) {
  const form = useForm<UserUpdateFormData>({
    resolver: zodResolver(userUpdateSchema),
    defaultValues: {
      email: user.email,
      full_name: user.full_name,
      is_active: user.is_active,
      is_superuser: user.is_superuser,
      password: '',
    },
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>编辑用户</CardTitle>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
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
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>新密码（留空表示不修改）</FormLabel>
                  <FormControl>
                    <Input type="password" placeholder="至少8个字符" {...field} value={field.value || ''} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="full_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>姓名</FormLabel>
                  <FormControl>
                    <Input {...field} value={field.value || ''} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="flex gap-4">
              <FormField
                control={form.control}
                name="is_active"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                    <div className="space-y-1 leading-none">
                      <FormLabel>激活用户</FormLabel>
                    </div>
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="is_superuser"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                    <div className="space-y-1 leading-none">
                      <FormLabel>超级管理员</FormLabel>
                    </div>
                  </FormItem>
                )}
              />
            </div>
            <Button type="submit" disabled={isLoading} className="w-full">
              {isLoading ? '更新中...' : '更新用户'}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
