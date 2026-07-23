import { TaskCreateForm } from "@/features/task";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export const metadata = {
  title: "发布任务",
  description: "管理员发布新任务",
};

/**
 * 管理员任务创建页面
 */
export default function AdminNewTaskPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">发布任务</h1>
        <p className="text-muted-foreground">管理员直接创建紧急/便捷任务</p>
      </div>

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>任务信息</CardTitle>
          <CardDescription>填写任务基本信息</CardDescription>
        </CardHeader>
        <CardContent>
          <TaskCreateForm />
        </CardContent>
      </Card>
    </div>
  );
}