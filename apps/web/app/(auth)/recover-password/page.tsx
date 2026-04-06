'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';

const formSchema = z.object({
  email: z.string().email('Invalid email address'),
});

type RecoverPasswordFormValues = z.infer<typeof formSchema>;

export default function RecoverPasswordPage() {
  const [isSubmitted, setIsSubmitted] = useState(false);

  const form = useForm<RecoverPasswordFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: '',
    },
  });

  async function onSubmit(values: RecoverPasswordFormValues) {
    // Note: The backend API doesn't have a direct recover-password endpoint
    // This is a placeholder that would typically send a password reset email
    // For now, we'll just show a success message
    toast.success('If an account exists with this email, you will receive password reset instructions.');
    setIsSubmitted(true);
  }

  if (isSubmitted) {
    return (
      <Card className="w-full">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl text-center">Check your email</CardTitle>
          <CardDescription className="text-center">
            We've sent password reset instructions to your email address.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-center">
          <p className="text-sm text-muted-foreground mb-4">
            If you don't see the email, check your spam folder or try again.
          </p>
          <Button variant="outline" asChild>
            <Link href="/login">Back to login</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl text-center">Forgot password?</CardTitle>
        <CardDescription className="text-center">
          Enter your email address and we'll send you a link to reset your password
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
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input placeholder="john@example.com" type="email" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button type="submit" className="w-full">
              Send reset link
            </Button>
          </form>
        </Form>

        <div className="mt-4 text-center text-sm">
          Remember your password?{' '}
          <Link href="/login" className="text-primary hover:underline">
            Sign in
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
