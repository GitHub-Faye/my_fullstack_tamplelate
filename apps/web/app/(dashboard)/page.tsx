'use client';

import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Package, Users, Settings, Shield } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { readUserMeV1UsersUsersMeGet, readItemsV1ItemsItemsGet } from '@repo/sdk';
import type { UserPublic } from '@repo/sdk';

export default function DashboardPage() {
  const { data: user } = useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const response = await readUserMeV1UsersUsersMeGet();
      return response.data as UserPublic;
    },
  });

  const { data: itemsData } = useQuery({
    queryKey: ['items'],
    queryFn: async () => {
      const response = await readItemsV1ItemsItemsGet();
      return response.data;
    },
  });

  const isAdmin = user?.is_superuser;
  const itemCount = itemsData?.count || 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">
          Welcome back, {user?.full_name || user?.email || 'User'}!
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Items</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{itemCount}</div>
            <p className="text-xs text-muted-foreground">
              Items in your collection
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Account</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{isAdmin ? 'Admin' : 'User'}</div>
            <p className="text-xs text-muted-foreground">
              {user?.email}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Package className="h-5 w-5" />
              Items
            </CardTitle>
            <CardDescription>
              Manage your items and inventory
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild className="w-full">
              <Link href="/dashboard/items">View Items</Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Settings
            </CardTitle>
            <CardDescription>
              Manage your profile and preferences
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild className="w-full" variant="outline">
              <Link href="/dashboard/settings">Open Settings</Link>
            </Button>
          </CardContent>
        </Card>

        {isAdmin && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Admin
              </CardTitle>
              <CardDescription>
                Manage users and system settings
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild className="w-full" variant="secondary">
                <Link href="/dashboard/admin">Admin Panel</Link>
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
