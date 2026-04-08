'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useRegisterUser } from '@/features/user/api/queries';
import { userRegisterSchema, type UserRegisterFormData } from '@/features/user/schemas';

export default function SignupPage() {
  const router = useRouter();
  const registerUser = useRegisterUser();

  const form = useForm<UserRegisterFormData>({
    resolver: zodResolver(userRegisterSchema),
    defaultValues: {
      email: '',
      password: '',
      full_name: '',
    },
  });

  const onSubmit = (data: UserRegisterFormData) => {
    registerUser.mutate(data, {
      onSuccess: () => {
        router.push('/login');
      },
    });
  };

  return (
    <Card>
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl font-bold">注册</CardTitle>
        <CardDescription>
          创建一个新账户开始使用系统
        </CardDescription>
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
              name="full_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>姓名（可选）</FormLabel>
                  <FormControl>
                    <Input placeholder="您的姓名" {...field} value={field.value || ''} />
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
            <Button type="submit" className="w-full" disabled={registerUser.isPending}>
              {registerUser.isPending ? '注册中...' : '注册'}
            </Button>
          </form>
        </Form>
        <div className="mt-4 text-center text-sm">
          <span className="text-muted-foreground">已有账户？ </span>
          <Link href="/login" className="text-primary hover:underline">
            立即登录
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
