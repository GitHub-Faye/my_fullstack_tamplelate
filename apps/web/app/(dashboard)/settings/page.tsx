'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  readUserMeV1UsersUsersMeGet,
  updateUserMeV1UsersUsersMePatch,
  updatePasswordMeV1UsersUsersMePasswordPatch,
} from '@repo/sdk';
import type { UserPublic, UserUpdateMe, UpdatePassword } from '@repo/sdk';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { useAuthStore } from '@/src/stores/auth';

const profileSchema = z.object({
  full_name: z.string().optional(),
  email: z.string().email(),
});

const passwordSchema = z.object({
  current_password: z.string().min(1, 'Current password is required'),
  new_password: z.string().min(8, 'Password must be at least 8 characters'),
  confirm_password: z.string().min(1, 'Please confirm your password'),
}).refine((data) => data.new_password === data.confirm_password, {
  message: "Passwords don't match",
  path: ["confirm_password"],
});

type ProfileFormValues = z.infer<typeof profileSchema>;
type PasswordFormValues = z.infer<typeof passwordSchema>;

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { setUser } = useAuthStore();
  const [activeTab, setActiveTab] = useState<'profile' | 'password'>('profile');

  const { data: user, isLoading } = useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const response = await readUserMeV1UsersUsersMeGet();
      const userData = response.data as UserPublic;
      setUser(userData);
      return userData;
    },
  });

  const updateProfileMutation = useMutation({
    mutationFn: async (values: UserUpdateMe) => {
      const response = await updateUserMeV1UsersUsersMePatch({
        body: values,
      });
      return response.data;
    },
    onSuccess: (data) => {
      toast.success('Profile updated successfully');
      setUser(data as UserPublic);
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
    },
    onError: (error) => {
      toast.error('Failed to update profile');
      console.error('Failed to update profile:', error);
    },
  });

  const updatePasswordMutation = useMutation({
    mutationFn: async (values: UpdatePassword) => {
      const response = await updatePasswordMeV1UsersUsersMePasswordPatch({
        body: values,
      });
      return response.data;
    },
    onSuccess: () => {
      toast.success('Password updated successfully');
      passwordForm.reset();
    },
    onError: (error) => {
      toast.error('Failed to update password');
      console.error('Failed to update password:', error);
    },
  });

  const profileForm = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      full_name: '',
      email: '',
    },
  });

  const passwordForm = useForm<PasswordFormValues>({
    resolver: zodResolver(passwordSchema),
    defaultValues: {
      current_password: '',
      new_password: '',
      confirm_password: '',
    },
  });

  // Update form values when user data is loaded
  useState(() => {
    if (user) {
      profileForm.reset({
        full_name: user.full_name || '',
        email: user.email,
      });
    }
  });

  // Set form values when user data is loaded
  if (user && !profileForm.formState.isDirty) {
    profileForm.setValue('full_name', user.full_name || '');
    profileForm.setValue('email', user.email);
  }

  function onProfileSubmit(values: ProfileFormValues) {
    const updateData: UserUpdateMe = {
      full_name: values.full_name || null,
      email: values.email,
    };
    updateProfileMutation.mutate(updateData);
  }

  function onPasswordSubmit(values: PasswordFormValues) {
    const passwordData: UpdatePassword = {
      current_password: values.current_password,
      new_password: values.new_password,
    };
    updatePasswordMutation.mutate(passwordData);
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Settings</h1>

      <div className="flex space-x-4 border-b">
        <button
          className={`pb-2 px-1 ${activeTab === 'profile'
            ? 'border-b-2 border-primary font-medium'
            : 'text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => setActiveTab('profile')}
        >
          Profile
        </button>
        <button
          className={`pb-2 px-1 ${activeTab === 'password'
            ? 'border-b-2 border-primary font-medium'
            : 'text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => setActiveTab('password')}
        >
          Password
        </button>
      </div>

      {activeTab === 'profile' && (
        <Card>
          <CardHeader>
            <CardTitle>Profile Information</CardTitle>
          </CardHeader>
          <CardContent>
            <Form {...profileForm}>
              <form onSubmit={profileForm.handleSubmit(onProfileSubmit)} className="space-y-6">
                <FormField
                  control={profileForm.control}
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
                  control={profileForm.control}
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

                <div className="flex justify-end">
                  <Button type="submit" disabled={updateProfileMutation.isPending}>
                    {updateProfileMutation.isPending ? 'Saving...' : 'Save Changes'}
                  </Button>
                </div>
              </form>
            </Form>
          </CardContent>
        </Card>
      )}

      {activeTab === 'password' && (
        <Card>
          <CardHeader>
            <CardTitle>Change Password</CardTitle>
          </CardHeader>
          <CardContent>
            <Form {...passwordForm}>
              <form onSubmit={passwordForm.handleSubmit(onPasswordSubmit)} className="space-y-6">
                <FormField
                  control={passwordForm.control}
                  name="current_password"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Current Password</FormLabel>
                      <FormControl>
                        <Input type="password" placeholder="••••••••" {...field} />
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
                      <FormLabel>New Password</FormLabel>
                      <FormControl>
                        <Input type="password" placeholder="••••••••" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={passwordForm.control}
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

                <div className="flex justify-end">
                  <Button type="submit" disabled={updatePasswordMutation.isPending}>
                    {updatePasswordMutation.isPending ? 'Updating...' : 'Update Password'}
                  </Button>
                </div>
              </form>
            </Form>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
