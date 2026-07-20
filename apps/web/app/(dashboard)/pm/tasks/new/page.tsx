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
  description: "发布新任务",
};

/**
 * 任务创建页面
 */
export default function NewTaskPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">发布任务</h1>
        <p className="text-muted-foreground">发布新任务需求</p>
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