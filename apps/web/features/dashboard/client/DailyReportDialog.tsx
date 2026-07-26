"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Loader2 } from "lucide-react";
import { useTasks } from "@/features/task/api";
import {
  createDailyReportV1DailyReportsPost,
  type TaskPublic,
} from "@repo/sdk";
import {
  TaskStatus as TaskStatusConst,
} from "@repo/contracts";
import { useCurrentUser } from "@/features/user";
import { useQueryClient } from "@tanstack/react-query";
import { taskKeys } from "@/features/task/api";
import { toast } from "sonner";

/** 日报表单条目 */
interface DailyReportEntry {
  taskId: string;
  taskName: string;
  T_reported: number | null;
  T_actual: number | null;
  todayHours: string;
  currentStage: string;
  progress: string;
  notes: string;
}

/** 预览计算结果（提交后由后端返回） */
interface SubmitResult {
  taskName: string;
  completionJudgment: string | null;
  starpointChange: number | null;
}

/**
 * 工作汇报弹窗（日报提交）
 *
 * 展示所有进行中任务，每行可填今日投入、阶段、进度、说明
 * 完成判定和预计星点由后端自动计算，提交后在结果中回显
 * 阶段仅可选：开发中、测试中、已完成（暂停中通过暂停按钮触发）
 */
export function DailyReportDialog({
  open,
  onOpenChange,
  onSuccess,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}) {
  const user = useCurrentUser();
  const queryClient = useQueryClient();
  const [summary, setSummary] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitResults, setSubmitResults] = useState<SubmitResult[] | null>(null);

  const { data: tasks, isLoading, refetch } = useTasks({
    page: 1,
    page_size: 50,
    engineer_id: user?.id,
    status: TaskStatusConst.IN_PROGRESS,
  } as any);

  useEffect(() => {
    if (open) {
      refetch();
    }
  }, [open, refetch]);

  const taskList = (tasks?.data as TaskPublic[]) || [];

  const [entries, setEntries] = useState<DailyReportEntry[]>([]);

  useEffect(() => {
    if (open && taskList.length > 0) {
      setEntries((prev) => {
        const prevMap = new Map(prev.map((e) => [e.taskId, e]));
        const merged = taskList.map((t) => {
          const existing = prevMap.get(t.id);
          if (existing) return existing;
          return {
            taskId: t.id,
            taskName: t.name,
            T_reported: t.T_reported ?? null,
            T_actual: t.T_actual ?? null,
            todayHours: "",
            currentStage: "developing",
            progress: t.progress ?? "",
            notes: "",
          };
        });
        return merged;
      });
    }
    if (!open) {
      setEntries([]);
      setSummary("");
      setSubmitResults(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, tasks?.data]);

  const updateEntry = (taskId: string, field: keyof DailyReportEntry, value: string) => {
    setEntries((prev) =>
      prev.map((e) => {
        if (e.taskId !== taskId) return e;
        const updated = { ...e, [field]: value };
        // 阶段选"已完成"时，自动设进度为 100%
        if (field === "currentStage" && value === "completed") {
          updated.progress = "100%";
        }
        return updated;
      })
    );
  };

  /** 判断进度 input 是否为禁用状态 */
  function isProgressDisabled(entry: DailyReportEntry): boolean {
    return entry.currentStage === "completed";
  }

  const handleSubmit = async () => {
    setSubmitting(true);
    const results: SubmitResult[] = [];
    for (const entry of entries) {
      const hours = parseFloat(entry.todayHours);
      if (isNaN(hours) || hours <= 0) {
        toast.error(`请为 "${entry.taskName}" 填写今日投入工时`);
        continue;
      }
      try {
        const res = await createDailyReportV1DailyReportsPost({
          throwOnError: true,
          body: {
            task_id: entry.taskId,
            today_hours: hours,
            current_stage: entry.currentStage as any,
            progress: entry.progress || undefined,
            notes: entry.notes || undefined,
            summary: summary || undefined,
            has_blocker: false,
          },
        });
        const data = res.data as any;
        results.push({
          taskName: entry.taskName,
          completionJudgment: data?.completion_judgment ?? null,
          starpointChange: data?.starpoint_change ?? null,
        });
      } catch (e: any) {
        toast.error(`"${entry.taskName}" 提交失败: ${e.message}`);
      }
    }
    if (results.length > 0) {
      setSubmitResults(results);
      toast.success(`${results.length} 个任务日报已提交`);
      // 刷新任务列表（完成的任务状态已变更）
      queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
      onSuccess?.();
    }
    setSubmitting(false);
  };

  /** 提交结果弹窗内容 */
  function renderSubmitResults() {
    if (!submitResults || submitResults.length === 0) return null;
    return (
      <div className="mt-4 rounded-md border overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-muted-foreground bg-muted/50">
              <th className="text-left px-3 py-2 font-medium whitespace-nowrap">任务</th>
              <th className="text-left px-3 py-2 font-medium whitespace-nowrap">完成判定</th>
              <th className="text-left px-3 py-2 font-medium whitespace-nowrap">星点变化</th>
            </tr>
          </thead>
          <tbody>
            {submitResults.map((r, i) => (
              <tr key={i} className="border-b last:border-0">
                <td className="px-3 py-2 font-medium">{r.taskName}</td>
                <td className="px-3 py-2">{r.completionJudgment ?? "-"}</td>
                <td className="px-3 py-2">
                  {r.starpointChange != null ? (
                    <span className={r.starpointChange >= 0 ? "text-green-600" : "text-red-600"}>
                      {r.starpointChange >= 0 ? `+${r.starpointChange}` : r.starpointChange}
                    </span>
                  ) : "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>工作汇报</DialogTitle>
          <DialogDescription>提交今日工作日报</DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : submitResults ? (
          <>
            <p className="text-sm text-muted-foreground mb-2">日报已提交，完成判定与星点变化如下：</p>
            {renderSubmitResults()}
            <div className="flex justify-end gap-2 mt-4">
              <Button onClick={() => { setSubmitResults(null); onOpenChange(false); }}>
                关闭
              </Button>
            </div>
          </>
        ) : entries.length === 0 ? (
          <p className="text-center py-8 text-muted-foreground">
            {taskList.length === 0 ? "暂无进行中任务" : "请先填写任务信息"}
          </p>
        ) : (
          <>
            {/* 日报表格 */}
            <div className="rounded-md border overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-muted-foreground bg-muted/50">
                    <th className="text-left px-3 py-2 font-medium whitespace-nowrap">进行中任务</th>
                    <th className="text-left px-3 py-2 font-medium whitespace-nowrap">T报</th>
                    <th className="text-left px-3 py-2 font-medium whitespace-nowrap">T实</th>
                    <th className="text-left px-3 py-2 font-medium whitespace-nowrap">今日投入</th>
                    <th className="text-left px-3 py-2 font-medium whitespace-nowrap">当前阶段</th>
                    <th className="text-left px-3 py-2 font-medium whitespace-nowrap">当前进度</th>
                    <th className="text-left px-3 py-2 font-medium whitespace-nowrap">说明</th>
                  </tr>
                </thead>
                <tbody>
                  {entries.map((entry) => (
                    <tr key={entry.taskId} className="border-b last:border-0">
                      <td className="px-3 py-2 font-medium max-w-[120px] truncate">
                        {entry.taskName}
                      </td>
                      <td className="px-3 py-2 text-muted-foreground">
                        {entry.T_reported != null ? `${entry.T_reported}h` : "-"}
                      </td>
                      <td className="px-3 py-2 text-muted-foreground">
                        {entry.T_actual != null ? `${entry.T_actual}h` : "-"}
                      </td>
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-1">
                          <Input
                            type="number"
                            min="0"
                            step="0.5"
                            className="w-16 h-8 text-sm"
                            placeholder="h"
                            value={entry.todayHours}
                            onChange={(e) =>
                              updateEntry(entry.taskId, "todayHours", e.target.value)
                            }
                          />
                          <span className="text-xs text-muted-foreground">h</span>
                        </div>
                      </td>
                      <td className="px-3 py-2">
                        <Select
                          value={entry.currentStage}
                          onValueChange={(v) =>
                            updateEntry(entry.taskId, "currentStage", v)
                          }
                        >
                          <SelectTrigger className="w-[90px] h-8">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="developing">开发中</SelectItem>
                            <SelectItem value="testing">测试中</SelectItem>
                            <SelectItem value="completed">已完成</SelectItem>
                          </SelectContent>
                        </Select>
                      </td>
                      <td className="px-3 py-2">
                        <Input
                          className={`w-16 h-8 text-sm ${isProgressDisabled(entry) ? "bg-muted" : ""}`}
                          placeholder="%"
                          value={entry.progress}
                          disabled={isProgressDisabled(entry)}
                          onChange={(e) =>
                            updateEntry(entry.taskId, "progress", e.target.value)
                          }
                        />
                      </td>
                      <td className="px-3 py-2">
                        <Input
                          className="w-[120px] h-8 text-sm"
                          placeholder="说明"
                          value={entry.notes}
                          onChange={(e) =>
                            updateEntry(entry.taskId, "notes", e.target.value)
                          }
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* 底部表单 */}
            <div className="space-y-3 mt-4">
              <div>
                <label className="text-sm text-muted-foreground block mb-1">
                  今日总结
                </label>
                <Textarea
                  placeholder="今日主要工作内容..."
                  value={summary}
                  onChange={(e) => setSummary(e.target.value)}
                />
              </div>
            </div>

            {/* 提交按钮 */}
            <div className="flex justify-end gap-2 mt-4">
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                取消
              </Button>
              <Button onClick={handleSubmit} disabled={submitting}>
                {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                提交日报
              </Button>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
