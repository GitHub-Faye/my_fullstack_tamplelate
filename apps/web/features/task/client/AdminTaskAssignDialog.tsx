"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { reassignTaskV1TasksTaskIdReassignPost, type EngineerLoad } from "@repo/sdk";
import { useAdminDashboard } from "@/features/dashboard/api/client/queries";
import { adminTaskKeys } from "../api/client/adminMutations";

interface AdminTaskAssignDialogProps {
  taskId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/**
 * 改派工程师弹窗
 *
 * 管理员选择新工程师并填写 T报，提交后改派工程师并更新 T报。
 * 工程师负载数据复用 GET /v1/dashboard/admin 返回的 engineer_loads。
 */
export function AdminTaskAssignDialog({
  taskId,
  open,
  onOpenChange,
}: AdminTaskAssignDialogProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: dashboard, isLoading: loadingLoads } = useAdminDashboard();

  const [selectedEngineerId, setSelectedEngineerId] = useState<string>("");
  const [T_reported, setT_reported] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);

  const engineerLoads: EngineerLoad[] = (dashboard as any)?.engineer_loads ?? [];

  const handleSubmit = async () => {
    if (!selectedEngineerId) {
      toast.error("请选择工程师");
      return;
    }

    setSubmitting(true);
    try {
      await reassignTaskV1TasksTaskIdReassignPost({
        path: { task_id: taskId },
        body: {
          new_engineer_id: selectedEngineerId,
          ...(T_reported ? { T_reported: parseFloat(T_reported) } : {}),
        },
        throwOnError: true,
      });
      toast.success("改派成功");
      queryClient.invalidateQueries({ queryKey: adminTaskKeys.all });
      onOpenChange(false);
      router.replace(`/admin/tasks/${taskId}`);
    } catch (error: any) {
      toast.error(error.message || "改派失败");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>改派工程师</DialogTitle>
          <DialogDescription>选择新的工程师并填写 T报</DialogDescription>
        </DialogHeader>

        {loadingLoads ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : engineerLoads.length === 0 ? (
          <p className="text-center py-8 text-muted-foreground">暂无工程师数据</p>
        ) : (
          <div className="space-y-6">
            <RadioGroup
              value={selectedEngineerId}
              onValueChange={setSelectedEngineerId}
            >
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-muted-foreground">
                    <th className="text-left px-3 py-2 font-medium w-10" />
                    <th className="text-left px-3 py-2 font-medium">工程师</th>
                    <th className="text-center px-3 py-2 font-medium">持有任务</th>
                    <th className="text-center px-3 py-2 font-medium">T月剩余</th>
                    <th className="text-center px-3 py-2 font-medium">准确率</th>
                    <th className="text-center px-3 py-2 font-medium">T报</th>
                  </tr>
                </thead>
                <tbody>
                  {engineerLoads.map((eng: EngineerLoad) => {
                    const isSelected = selectedEngineerId === eng.user_id;
                    return (
                      <tr
                        key={eng.user_id}
                        className={`border-b last:border-0 ${isSelected ? "bg-muted/50" : ""}`}
                      >
                        <td className="px-3 py-2">
                          <RadioGroupItem
                            value={eng.user_id}
                            id={eng.user_id}
                          />
                        </td>
                        <td className="px-3 py-2">
                          <Label htmlFor={eng.user_id} className="cursor-pointer">
                            {eng.full_name ?? eng.user_id.slice(0, 8)}
                          </Label>
                        </td>
                        <td className="px-3 py-2 text-center">{eng.current_tasks}</td>
                        <td className="px-3 py-2 text-center">{eng.T_remaining}h</td>
                        <td className="px-3 py-2 text-center">{eng.accuracy_rate}%</td>
                        <td className="px-3 py-2 text-center">
                          <Input
                            type="number"
                            step="0.1"
                            min="0"
                            className="w-20 h-8 text-center mx-auto"
                            placeholder="h"
                            disabled={!isSelected}
                            value={isSelected ? T_reported : ""}
                            onChange={(e) => setT_reported(e.target.value)}
                            onClick={() => {
                              if (!isSelected) {
                                setSelectedEngineerId(eng.user_id);
                              }
                            }}
                          />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </RadioGroup>
          </div>
        )}

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={submitting}
          >
            取消
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!selectedEngineerId || submitting || loadingLoads}
          >
            {submitting ? "改派中..." : "确认改派"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}