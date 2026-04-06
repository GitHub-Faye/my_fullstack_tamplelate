'use client';

import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { createUserV1UsersUsersPost } from '@repo/sdk';
import type { UserCreate } from '@repo/sdk';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

const formSchema = z.object({
  full_name: z.string().optional(),
  email: z.string().email(),
  password: z.string().min(8),
  is_superuser: z.boolean(),
});

type UserFormValues = z.infer<typeof formSchema>;

export default function NewUserPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: async (values: UserCreate) => {
      const response = await createUserV1UsersUsersPost({
        body: values
      });
      return response.data;
    },
    onSuccess: (data) => {
      toast.success('User created successfully');
      queryClient.invalidateQueries({ queryKey: ['users'] });
      router.push(`/dashboard/admin`);
    },
    onError: (error) => {
      toast.error('Failed to create user');
      console.error('Failed to create user:', error);
    }
  });

  const form = useForm<UserFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      full_name: '',
      email: '',
      password: '',
      is_superuser: false,
    },
  });

  async function onSubmit(values: UserFormValues) {
    const userData: UserCreate = {
      email: values.email,
      password: values.password,
      full_name: values.full_name || null,
      is_superuser: values.is_superuser,
    };
    createMutation.mutate(userData);
  }

  return (
    <div className="container max-w-4xl py-6">
      <Card>
        <CardHeader>
          <CardTitle>Create New User</CardTitle>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
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
                      <Input placeholder="••••••••" type="password" {...field} />
                    </FormControl>
                    <FormMessage />
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
                      <FormLabel>Admin User</FormLabel>
                    </div>
                  </FormItem>
                )}
              />

              <div className="flex justify-end space-x-4">
                <Button type="button" variant="outline" onClick={() => router.back()}>
                  Cancel
                </Button>
                <Button type="submit" disabled={createMutation.isPending}>
                  {createMutation.isPending ? 'Creating...' : 'Create User'}
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}
