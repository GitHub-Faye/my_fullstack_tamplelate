'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import { Menu, User, Settings, Users, LayoutDashboard, LogOut, Package } from 'lucide-react';
import { useCurrentUser } from '../api/queries';
import { useAuthStore } from '@/src/stores/auth';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

const navItems = [
  { href: '/dashboard', label: 'Overview', icon: LayoutDashboard },
  { href: '/dashboard/items', label: 'Items', icon: Package },
  { href: '/dashboard/admin', label: 'User Management', icon: Users, adminOnly: true },
  { href: '/dashboard/settings', label: 'Settings', icon: Settings },
];

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const pathname = usePathname();
  const { data: user } = useCurrentUser();
  const logout = useAuthStore((state) => state.logout);

  const handleLogout = () => {
    // Clear cookie
    document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    logout();
    window.location.href = '/login';
  };

  const filteredNavItems = navItems.filter(
    (item) => !item.adminOnly || user?.is_superuser
  );

  return (
    <div className="flex min-h-screen">
      {/* Sidebar for desktop */}
      <aside className="hidden lg:flex w-64 flex-col border-r bg-background">
        <div className="flex h-14 items-center border-b px-4">
          <Link href="/dashboard" className="flex items-center gap-2 font-semibold">
            <LayoutDashboard className="h-5 w-5" />
            <span>Dashboard</span>
          </Link>
        </div>
        <nav className="flex-1 overflow-auto py-4">
          <div className="px-3 space-y-1">
            {filteredNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </div>
        </nav>
        <div className="border-t p-4">
          <div className="flex items-center gap-3">
            <Avatar className="h-8 w-8">
              <AvatarFallback>
                {user?.full_name?.charAt(0) || user?.email?.charAt(0).toUpperCase() || 'U'}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 overflow-hidden">
              <p className="text-sm font-medium truncate">
                {user?.full_name || user?.email || 'Loading...'}
              </p>
              <p className="text-xs text-muted-foreground truncate">
                {user?.is_superuser ? 'Super Admin' : 'User'}
              </p>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile header */}
      <div className="flex flex-col flex-1">
        <header className="flex h-14 items-center gap-4 border-b bg-background px-4 lg:hidden">
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-64">
              <div className="flex h-14 items-center border-b px-4">
                <Link href="/dashboard" className="flex items-center gap-2 font-semibold">
                  <LayoutDashboard className="h-5 w-5" />
                  <span>Dashboard</span>
                </Link>
              </div>
              <nav className="flex-1 py-4">
                <div className="px-3 space-y-1">
                  {filteredNavItems.map((item) => {
                    const Icon = item.icon;
                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                      >
                        <Icon className="h-4 w-4" />
                        {item.label}
                      </Link>
                    );
                  })}
                </div>
              </nav>
            </SheetContent>
          </Sheet>
          <span className="font-semibold">Dashboard</span>
          <div className="flex-1" />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <Avatar className="h-8 w-8">
                  <AvatarFallback>
                    {user?.full_name?.charAt(0) || user?.email?.charAt(0).toUpperCase() || 'U'}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>My Account</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link href="/dashboard/settings">
                  <Settings className="mr-2 h-4 w-4" />
                  Settings
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </header>

        {/* Desktop header */}
        <header className="hidden lg:flex h-14 items-center justify-end gap-4 border-b bg-background px-6">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="flex items-center gap-2">
                <Avatar className="h-8 w-8">
                  <AvatarFallback>
                    {user?.full_name?.charAt(0) || user?.email?.charAt(0).toUpperCase() || 'U'}
                  </AvatarFallback>
                </Avatar>
                <span className="text-sm font-medium">
                  {user?.full_name || user?.email || 'Loading...'}
                </span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>My Account</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link href="/dashboard/settings">
                  <Settings className="mr-2 h-4 w-4" />
                  Settings
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </header>

        {/* Main content */}
        <main className="flex-1 p-4 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
