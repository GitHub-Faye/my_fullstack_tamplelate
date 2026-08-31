import { RoleForm } from "@/features/role/client/RoleForm";

export const metadata = {
  title: "新建角色",
  description: "创建新角色",
};

export default function NewRolePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">新建角色</h1>
        <p className="text-muted-foreground">创建一个新的角色并分配权限</p>
      </div>

      <RoleForm mode="create" />
    </div>
  );
}