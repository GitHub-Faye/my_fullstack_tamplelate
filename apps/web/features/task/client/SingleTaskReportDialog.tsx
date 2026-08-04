"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import {
  createDailyReportV1DailyReportsPost,
  type TaskPublic,
} from "@repo/sdk";
import { toast } from "sonner";

/** 单任务日报提交回显结果 */
interface ReportResult {
  completionJudgment: string | null;
  starpointChange: string | null;
  newTActual: number | null;
}

/**
 * 单任务日报弹窗
 *
 * 在工程师"我的任务"中，针对单个进行中任务提交日报。
 * 同一任务同一天允许多次提交（不覆盖），每次录入独立投入工时，
 * 后端会将本次 today_hours 累加到任务 T_actual。
 */
export function SingleTaskReportDialog({
  task,
  open,
  onOpenChange,
  onSuccess,
}: {
  task: TaskPublic;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}) {
  const [todayHours, setTodayHours] = useState("");
  const [currentStage, setCurrentStage] = useState("developing");
  const [progress, setProgress] = useState(task.progress ?? "");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<ReportResult | null>(null);

  /** 阶段是否为已完成（此时进度自动设为 100% 并禁用输入） */
  const isCompleted = currentStage === "completed";

  const reset = () => {
    setTodayHours("");
    setCurrentStage("developing");
    setProgress(task.progress ?? "");
    setNotes("");
    setResult(null);
  };

  /** 关闭弹窗时重置表单 */
  function handleOpenChange(open: boolean) {
    if (!open) reset();
    onOpenChange(open);
  }

  const handleSubmit = async () => {
    const hours = parseFloat(todayHours);
    if (isNaN(hours) || hours <= 0) {
      toast.error("请填写今日投入工时");
      return;
    }
    setSubmitting(true);
    try {
      const res = await createDailyReportV1DailyReportsPost({
        throwOnError: true,
        body: {
          task_id: task.id,
          today_hours: hours,
          current_stage: currentStage as any,
          progress: isCompleted ? "100%" : progress || undefined,
          notes: notes || undefined,
          has_blocker: false,
        },
      });
      const data = res.data as any;
      setResult({
        completionJudgment: data?.completion_judgment ?? null,
        starpointChange:
          data?.starpoint_change != null
            ? `${data.starpoint_change >= 0 ? "+" : ""}${data.starpoint_change}`
            : null,
        newTActual: data?.T_actual ?? task.T_actual ?? null,
      });
      toast.success("日报已提交");
      onSuccess?.();
    } catch (e: any) {
      toast.error(e.message || "提交失败");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>日报提交 - {task.name}</DialogTitle>
          <DialogDescription>
            为该任务提交今日工作日报（同一任务同一天可多次提交，每次独立记录投入）
          </DialogDescription>
        </DialogHeader>

        {result ? (
          <div className="space-y-4">
            <p className="text-sm text-green-600">日报已提交，完成判定与星点变化如下：</p>
            <div className="rounded-md border">
              <table className="w-full text-sm">
                <tbody>
                  <tr className="border-b">
                    <td className="px-3 py-2 text-muted-foreground">完成判定</td>
                    <td className="px-3 py-2">{result.completionJudgment ?? "-"}</td>
                  </tr>
                  <tr className="border-b">
                    <td className="px-3 py-2 text-muted-foreground">星点变化</td>
                    <td className={`px-3 py-2 ${result.starpointChange && !result.starpointChange.startsWith("-") ? "text-green-600" : "text-red-600"}`}>
                      {result.starpointChange ?? "-"}
                    </td>
                  </tr>
                  <tr>
                    <td className="px-3 py-2 text-muted-foreground">任务累计T实</td>
                    <td className="px-3 py-2">
                      {result.newTActual != null ? `${result.newTActual}h` : "-"}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div className="flex justify-end">
              <Button onClick={() => handleOpenChange(false)}>关闭</Button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {/* 任务信息 */}
            <div className="rounded-md border p-3 text-sm space-y-1">
              <div className="flex justify-between">
                <span className="text-muted-foreground">T报</span>
                <span>{task.T_reported != null ? `${task.T_reported}h` : "-"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">当前T实</span>
                <span>{task.T_actual != null ? `${task.T_actual}h` : "-"}</span>
              </div>
            </div>

            {/* 今日投入工时 */}
            <div>
              <label className="text-sm text-muted-foreground block mb-1">今日投入工时（小时）</label>
              <div className="flex items-center gap-1">
                <Input
                  type="number"
                  min="0"
                  step="0.5"
                  className="w-24"
                  placeholder="h"
                  value={todayHours}
                  onChange={(e) => setTodayHours(e.target.value)}
                />
                <span className="text-xs text-muted-foreground">h</span>
              </div>
            </div>

            {/* 当前阶段 */}
            <div>
              <label className="text-sm text-muted-foreground block mb-1">当前阶段</label>
              <Select value={currentStage} onValueChange={setCurrentStage}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="developing">开发中</SelectItem>
                  <SelectItem value="testing">测试中</SelectItem>
                  <SelectItem value="completed">已完成</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* 当前进度 */}
            <div>
              <label className="text-sm text-muted-foreground block mb-1">当前进度</label>
              <div className="flex items-center gap-1">
                <Input
                  className={`w-24 ${isCompleted ? "bg-muted" : ""}`}
                  placeholder="%"
                  value={isCompleted ? "100" : progress}
                  disabled={isCompleted}
                  onChange={(e) => setProgress(e.target.value)}
                />
                <span className="text-xs text-muted-foreground">%</span>
              </div>
            </div>

            {/* 说明 */}
            <div>
              <label className="text-sm text-muted-foreground block mb-1">说明</label>
              <Textarea
                placeholder="本次工作内容说明..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>

            {/* 提交按钮 */}
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => handleOpenChange(false)}>
                取消
              </Button>
              <Button onClick={handleSubmit} disabled={submitting}>
                {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                提交日报
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
