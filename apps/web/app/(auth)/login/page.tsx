'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
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
import { useAuthStore } from '@/src/stores/auth';
import { loginAccessTokenV1LoginAccessTokenPost, readUserMeV1UsersMeGet } from '@/src/lib/api-sdk';
import { toast } from 'sonner';

// Helper to set cookie
function setCookie(name: string, value: string, days: number) {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
}

const loginSchema = z.object({
  email: z.string().email('请输入有效的邮箱地址'),
  password: z.string().min(1, '请输入密码'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const setToken = useAuthStore((state) => state.setToken);
  const setUser = useAuthStore((state) => state.setUser);

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      // Login and get token
      const loginResponse = await loginAccessTokenV1LoginAccessTokenPost({
        body: {
          username: data.email,
          password: data.password,
        },
      });

      if (loginResponse.error) {
        toast.error('登录失败，请检查邮箱和密码');
        return;
      }

      const token = loginResponse.data.access_token;
      setToken(token);

      // Store token in localStorage for API client
      localStorage.setItem('access_token', token);
      
      // Also set cookie for middleware auth check
      setCookie('access_token', token, 7);

      // Get user info
      const userResponse = await readUserMeV1UsersMeGet();
      
      if (userResponse.data) {
        setUser(userResponse.data);
      }

      toast.success('登录成功');
      router.push('/dashboard');
    } catch (error) {
      toast.error('登录失败，请稍后重试');
    }
  };

  return (
    <Card>
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl font-bold">登录</CardTitle>
        <CardDescription>
          输入您的邮箱和密码登录系统
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
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>密码</FormLabel>
                  <FormControl>
                    <Input type="password" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting ? '登录中...' : '登录'}
            </Button>
          </form>
        </Form>
        <div className="mt-4 text-center text-sm">
          <span className="text-muted-foreground">还没有账户？ </span>
          <Link href="/signup" className="text-primary hover:underline">
            立即注册
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
