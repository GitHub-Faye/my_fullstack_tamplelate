import { TaskEditForm } from "@/features/task";

export const metadata = {
  title: "编辑任务",
  description: "修改任务信息",
};

/**
 * 任务编辑页面
 */
export default async function TaskEditPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">编辑任务</h1>
        <p className="text-muted-foreground">修改任务信息</p>
      </div>

      <TaskEditForm taskId={id} />
    </div>
  );
}