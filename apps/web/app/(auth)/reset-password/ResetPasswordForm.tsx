'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { resetPasswordV1ResetPasswordPost } from '@repo/sdk';
import type { NewPassword } from '@repo/sdk';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';

const formSchema = z.object({
  new_password: z.string().min(8, 'Password must be at least 8 characters'),
  confirm_password: z.string(),
}).refine((data) => data.new_password === data.confirm_password, {
  message: "Passwords don't match",
  path: ["confirm_password"],
});

type ResetPasswordFormValues = z.infer<typeof formSchema>;

export default function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const tokenParam = searchParams.get('token');
    if (tokenParam) {
      setToken(tokenParam);
    }
  }, [searchParams]);

  const resetMutation = useMutation({
    mutationFn: async (values: NewPassword) => {
      const response = await resetPasswordV1ResetPasswordPost({
        body: values
      });
      return response.data;
    },
    onSuccess: () => {
      toast.success('Password reset successfully! Please log in with your new password.');
      router.push('/login');
    },
    onError: (error) => {
      toast.error('Failed to reset password');
      console.error('Failed to reset password:', error);
    }
  });

  const form = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      new_password: '',
      confirm_password: '',
    },
  });

  async function onSubmit(values: ResetPasswordFormValues) {
    if (!token) {
      toast.error('Invalid or missing reset token');
      return;
    }

    const passwordData: NewPassword = {
      token: token,
      new_password: values.new_password,
    };
    resetMutation.mutate(passwordData);
  }

  if (!token) {
    return (
      <Card className="w-full">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl text-center">Invalid Link</CardTitle>
          <CardDescription className="text-center">
            This password reset link is invalid or has expired.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-center">
          <Button asChild>
            <Link href="/recover-password">Request new link</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl text-center">Reset your password</CardTitle>
        <CardDescription className="text-center">
          Enter your new password below
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="new_password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>New Password</FormLabel>
                  <FormControl>
                    <Input type="password" placeholder="••••••••" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="confirm_password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Confirm New Password</FormLabel>
                  <FormControl>
                    <Input type="password" placeholder="••••••••" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button type="submit" className="w-full" disabled={resetMutation.isPending}>
              {resetMutation.isPending ? 'Resetting...' : 'Reset password'}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
