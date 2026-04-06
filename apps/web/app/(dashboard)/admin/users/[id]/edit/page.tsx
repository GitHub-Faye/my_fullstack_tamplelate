'use client';

import { useParams, useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  readUserByIdV1UsersUsersUserIdGet,
  updateUserV1UsersUsersUserIdPatch,
} from '@repo/sdk';
import type { UserPublic, UserUpdate } from '@repo/sdk';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

const formSchema = z.object({
  full_name: z.string().optional().nullable(),
  email: z.string().email(),
  is_superuser: z.boolean(),
  is_active: z.boolean(),
  password: z.string().min(8).optional().nullable(),
});

type UserFormValues = z.infer<typeof formSchema>;

export default function EditUserPage() {
  const { id } = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const userId = id as string;

  const { data: user, isLoading } = useQuery({
    queryKey: ['user', userId],
    queryFn: async () => {
      const response = await readUserByIdV1UsersUsersUserIdGet({
        path: { user_id: userId },
      });
      return response.data as UserPublic;
    },
  });

  const updateMutation = useMutation({
    mutationFn: async (values: UserUpdate) => {
      const response = await updateUserV1UsersUsersUserIdPatch({
        body: values,
        path: { user_id: userId },
      });
      return response.data;
    },
    onSuccess: () => {
      toast.success('User updated successfully');
      queryClient.invalidateQueries({ queryKey: ['user', userId] });
      queryClient.invalidateQueries({ queryKey: ['users'] });
      router.push('/dashboard/admin');
    },
    onError: (error) => {
      toast.error('Failed to update user');
      console.error('Failed to update user:', error);
    },
  });

  const form = useForm<UserFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      full_name: '',
      email: '',
      is_superuser: false,
      is_active: true,
      password: null,
    },
  });

  useEffect(() => {
    if (user) {
      form.reset({
        full_name: user.full_name,
        email: user.email,
        is_superuser: user.is_superuser || false,
        is_active: user.is_active !== false,
        password: null,
      });
    }
  }, [user, form]);

  function onSubmit(values: UserFormValues) {
    const updateData: UserUpdate = {
      full_name: values.full_name,
      email: values.email,
      is_superuser: values.is_superuser,
      is_active: values.is_active,
    };
    if (values.password) {
      updateData.password = values.password;
    }
    updateMutation.mutate(updateData);
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="container max-w-4xl py-6">
      <Card>
        <CardHeader>
          <CardTitle>Edit User</CardTitle>
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
                      <Input placeholder="John Doe" {...field} value={field.value || ''} />
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
                    <FormLabel>New Password (leave empty to keep current)</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="••••••••"
                        type="password"
                        {...field}
                        value={field.value || ''}
                        onChange={(e) => field.onChange(e.target.value || null)}
                      />
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
                      <FormLabel>Active</FormLabel>
                    </div>
                  </FormItem>
                )}
              />

              <div className="flex justify-end space-x-4">
                <Button type="button" variant="outline" onClick={() => router.back()}>
                  Cancel
                </Button>
                <Button type="submit" disabled={updateMutation.isPending}>
                  {updateMutation.isPending ? 'Updating...' : 'Update User'}
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}
