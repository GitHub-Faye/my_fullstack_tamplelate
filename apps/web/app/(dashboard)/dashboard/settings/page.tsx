"use client";

import { useAuthUser } from "@/features/user";
import { UserProfileForm, PasswordChangeForm } from "@/features/user";

export default function SettingsPage() {
  const user = useAuthUser();

  if (!user) {
    return null;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">设置</h1>
        <p className="text-sm text-muted-foreground">管理您的账户设置</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <UserProfileForm user={user} />
        <PasswordChangeForm />
      </div>
    </div>
  );
}