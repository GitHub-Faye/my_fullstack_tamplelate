import { DashboardLayout } from 'features/user/components/DashboardLayout';

export default function Layout({ children }: { children: React.ReactNode }) {
  return <DashboardLayout>{children}</DashboardLayout>;
}
