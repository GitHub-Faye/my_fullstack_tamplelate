"use client";

import { useUser } from "@/src/stores/auth";
import { UserProfileForm, PasswordChangeForm } from "@/features/user";

export default function SettingsPage() {
  const user = useUser();

  if (!user) {
    return null;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">设置</h1>
        <p className="text-muted-foreground">管理您的账户设置</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <UserProfileForm user={user} />
        <PasswordChangeForm />
      </div>
    </div>
  );
}
