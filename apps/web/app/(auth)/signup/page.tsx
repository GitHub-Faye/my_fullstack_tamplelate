'use client';

import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { registerUserV1UsersUsersSignupPost } from '@repo/sdk';
import type { UserRegister } from '@repo/sdk';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';

const formSchema = z.object({
  full_name: z.string().optional(),
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirm_password: z.string(),
}).refine((data) => data.password === data.confirm_password, {
  message: "Passwords don't match",
  path: ["confirm_password"],
});

type SignupFormValues = z.infer<typeof formSchema>;

export default function SignupPage() {
  const router = useRouter();

  const signupMutation = useMutation({
    mutationFn: async (values: UserRegister) => {
      const response = await registerUserV1UsersUsersSignupPost({
        body: values
      });
      return response.data;
    },
    onSuccess: () => {
      toast.success('Account created successfully! Please log in.');
      router.push('/login');
    },
    onError: (error) => {
      toast.error('Failed to create account');
      console.error('Failed to signup:', error);
    }
  });

  const form = useForm<SignupFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      full_name: '',
      email: '',
      password: '',
      confirm_password: '',
    },
  });

  async function onSubmit(values: SignupFormValues) {
    const userData: UserRegister = {
      email: values.email,
      password: values.password,
      full_name: values.full_name || null,
    };
    signupMutation.mutate(userData);
  }

  return (
    <Card className="w-full">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl text-center">Create an account</CardTitle>
        <CardDescription className="text-center">
          Enter your information to create your account
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="full_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Full Name</FormLabel>
                  <FormControl>
                    <Input placeholder="John Doe" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input placeholder="john@example.com" type="email" {...field} />
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
                  <FormLabel>Password</FormLabel>
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
                  <FormLabel>Confirm Password</FormLabel>
                  <FormControl>
                    <Input type="password" placeholder="••••••••" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button type="submit" className="w-full" disabled={signupMutation.isPending}>
              {signupMutation.isPending ? 'Creating account...' : 'Create account'}
            </Button>
          </form>
        </Form>

        <div className="mt-4 text-center text-sm">
          Already have an account?{' '}
          <Link href="/login" className="text-primary hover:underline">
            Sign in
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
