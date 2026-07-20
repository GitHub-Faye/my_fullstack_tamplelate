import { AdminTaskTable } from "@/features/task";

export const metadata = {
  title: "任务审核",
  description: "审核和管理任务",
};

/**
 * 管理员任务审核列表页面
 */
export default function AdminTasksPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">任务审核</h1>
        <p className="text-muted-foreground">审核和管理所有任务</p>
      </div>

      <AdminTaskTable />
    </div>
  );
}