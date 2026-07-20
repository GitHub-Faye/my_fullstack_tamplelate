import { TaskDetail } from "@/features/task";

export const metadata = {
  title: "任务详情",
  description: "查看任务详细信息",
};

/**
 * 任务详情页面
 */
export default async function TaskDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <div className="space-y-6">
      <TaskDetail taskId={id} />
    </div>
  );
}