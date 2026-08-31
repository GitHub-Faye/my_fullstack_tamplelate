import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export const metadata = {
  title: "找回密码",
  description: "找回密码",
};

export default function RecoverPasswordPage() {
  return (
    <div className="flex min-h-[70vh] items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold">找回密码</CardTitle>
          <CardDescription>该功能暂未接入后端</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            当前后端未实现密码重置接口（/v1/reset-password/ 已随模板清理移除），
            此页面暂为占位。如需密码重置能力，请在后端按统一规范新增对应业务域。
          </p>
          <Button variant="outline" className="w-full" asChild>
            <Link href="/login">
              <ArrowLeft className="mr-2 h-4 w-4" />
              返回登录
            </Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
