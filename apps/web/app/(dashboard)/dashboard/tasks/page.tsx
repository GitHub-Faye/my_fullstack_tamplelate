import { AdminTaskTable } from "@/features/task";

export const metadata = {
  title: "任务管理",
  description: "审核和管理所有任务",
};

/**
 * 管理员任务管理页面
 *
 * 调用 GET /v1/tasks/ 获取任务列表
 * 展示：11 列（任务、类型、发布人、工程师、预期上线、T报完成时间、T报/T实、报价倒计时、当前阶段/进度、状态、操作）
 */
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