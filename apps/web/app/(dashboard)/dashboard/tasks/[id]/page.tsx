import { AdminTaskDetail } from "@/features/task";

export const metadata = {
  title: "任务详情",
  description: "查看任务详情",
};

/**
 * 管理员任务详情页面
 */
export default async function AdminTaskDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <div className="space-y-6">
      <AdminTaskDetail taskId={id} />
    </div>
  );
}