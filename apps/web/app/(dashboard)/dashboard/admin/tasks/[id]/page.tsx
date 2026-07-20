import { AdminTaskDetail } from "@/features/task";

export const metadata = {
  title: "任务审核详情",
  description: "审核任务详情",
};

/**
 * 管理员任务审核详情页面
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