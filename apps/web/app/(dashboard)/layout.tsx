'use client';

import { ReactNode } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { useAuthStore } from '@/src/stores/auth';
import { useQuery } from '@tanstack/react-query';
import { readUserMeV1UsersUsersMeGet } from '@repo/sdk';
import type { UserPublic } from '@repo/sdk';
import {
  LayoutDashboard,
  Users,
  Package,
  Settings,
  Menu,
  LogOut,
  User,
  Shield,
} from 'lucide-react';

interface DashboardLayoutProps {
  children: ReactNode;
}

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Items', href: '/dashboard/items', icon: Package },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
];

const adminNavigation = [
  { name: 'User Management', href: '/dashboard/admin', icon: Shield },
];

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { logout, user: storedUser } = useAuthStore();

  const { data: user } = useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const response = await readUserMeV1UsersUsersMeGet();
      return response.data as UserPublic;
    },
    initialData: storedUser || undefined,
  });

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const isAdmin = user?.is_superuser;

  const NavLink = ({ item }: { item: { name: string; href: string; icon: React.ElementType } }) => {
    const Icon = item.icon;
    const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);

    return (
      <Link
        href={item.href}
        className={`flex items-center gap-3 rounded-lg px-3 py-2 transition-all ${
          isActive
            ? 'bg-primary text-primary-foreground'
            : 'text-muted-foreground hover:bg-muted hover:text-foreground'
        }`}
      >
        <Icon className="h-4 w-4" />
        {item.name}
      </Link>
    );
  };

  return (
    <div className="flex min-h-screen w-full">
      {/* Desktop Sidebar */}
      <aside className="hidden w-64 flex-col border-r bg-background lg:flex">
        <div className="flex h-14 items-center border-b px-4">
          <Link href="/dashboard" className="flex items-center gap-2 font-semibold">
            <Package className="h-6 w-6" />
            <span>My App</span>
          </Link>
        </div>
        <nav className="flex-1 overflow-auto py-4 px-3 space-y-6">
          <div className="space-y-1">
            {navigation.map((item) => (
              <NavLink key={item.name} item={item} />
            ))}
          </div>
          {isAdmin && (
            <div className="space-y-1">
              <div className="px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Admin
              </div>
              {adminNavigation.map((item) => (
                <NavLink key={item.name} item={item} />
              ))}
            </div>
          )}
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex flex-1 flex-col">
        {/* Header */}
        <header className="flex h-14 items-center gap-4 border-b bg-background px-4 lg:px-6">
          {/* Mobile Menu */}
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="outline" size="icon" className="lg:hidden">
                <Menu className="h-5 w-5" />
                <span className="sr-only">Toggle navigation</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-64 p-0">
              <div className="flex h-14 items-center border-b px-4">
                <Link href="/dashboard" className="flex items-center gap-2 font-semibold">
                  <Package className="h-6 w-6" />
                  <span>My App</span>
                </Link>
              </div>
              <nav className="flex-1 overflow-auto py-4 px-3 space-y-6">
                <div className="space-y-1">
                  {navigation.map((item) => (
                    <NavLink key={item.name} item={item} />
                  ))}
                </div>
                {isAdmin && (
                  <div className="space-y-1">
                    <div className="px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      Admin
                    </div>
                    {adminNavigation.map((item) => (
                      <NavLink key={item.name} item={item} />
                    ))}
                  </div>
                )}
              </nav>
            </SheetContent>
          </Sheet>

          <div className="flex-1" />

          {/* User Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                <Avatar className="h-8 w-8">
                  <AvatarFallback>
                    {user?.full_name?.charAt(0) || user?.email?.charAt(0) || 'U'}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end" forceMount>
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none">{user?.full_name || 'User'}</p>
                  <p className="text-xs leading-none text-muted-foreground">{user?.email}</p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link href="/dashboard/settings">
                  <Settings className="mr-2 h-4 w-4" />
                  Settings
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto p-4 lg:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
