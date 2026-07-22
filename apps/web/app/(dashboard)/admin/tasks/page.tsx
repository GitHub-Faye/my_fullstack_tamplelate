import { AdminTaskTable } from "@/features/task";

export const metadata = {
  title: "任务管理",
  description: "审核和管理所有任务",
};

export default function AdminTasksPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">任务管理</h1>
        <p className="text-muted-foreground">审核和管理所有任务</p>
      </div>
      <AdminTaskTable />
    </div>
  );
}