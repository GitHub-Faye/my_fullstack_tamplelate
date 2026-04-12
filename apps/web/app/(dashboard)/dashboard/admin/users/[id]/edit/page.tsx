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
        <h1 className="text-3xl font-bold">编辑用户</h1>
        <p className="text-muted-foreground">修改用户信息</p>
      </div>

      <UserDetail userId={id} />
    </div>
  );
}
