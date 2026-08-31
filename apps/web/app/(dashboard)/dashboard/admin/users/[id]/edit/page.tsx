import { UserDetail } from "@/features/user/server";

interface EditUserPageProps {
  params: Promise<{
    id: string;
  }>;
}

export default async function EditUserPage({ params }: EditUserPageProps) {
  const { id } = await params;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">编辑用户</h1>
        <p className="text-sm text-muted-foreground">修改用户信息</p>
      </div>

      <UserDetail userId={id} />
    </div>
  );
}