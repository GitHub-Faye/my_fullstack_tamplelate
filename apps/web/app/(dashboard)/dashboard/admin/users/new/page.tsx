import { UserForm } from "@/features/user/client";

export default function NewUserPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">创建用户</h1>
        <p className="text-sm text-muted-foreground">创建一个新的用户账户</p>
      </div>

      <UserForm mode="create" />
    </div>
  );
}