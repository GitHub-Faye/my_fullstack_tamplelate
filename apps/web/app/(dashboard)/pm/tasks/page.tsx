import { PMTaskTable } from "@/features/task";

export const metadata = {
  title: "PM任务管理",
  description: "管理您发布的任务",
};

/**
 * PM 任务列表页面
 */
export default function PMTasksPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">任务管理</h1>
        <p className="text-muted-foreground">管理您发布的所有任务</p>
      </div>

      <PMTaskTable />
    </div>
  );
}