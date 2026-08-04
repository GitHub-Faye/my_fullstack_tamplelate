"use client";

import { useState, useMemo } from "react";
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
import { reassignTaskV1TasksTaskIdReassignPost } from "@repo/sdk";
import { useUsers } from "@/features/user";
import { taskKeys } from "../api/client/queries";

interface PmTaskAssignDialogProps {
  taskId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/**
 * PM 指派工程师弹窗
 *
 * 竞拍中的任务，PM 可跳过竞价流程直接指定工程师。
 * 与 AdminTaskAssignDialog 类似，但使用 useUsers 获取工程师列表
 * （PM 无 dashboard:admin 权限，无法使用 useAdminDashboard）。
 */
export function PmTaskAssignDialog({
  taskId,
  open,
  onOpenChange,
}: PmTaskAssignDialogProps) {
  const queryClient = useQueryClient();
  const { data: usersData, isLoading: loadingUsers } = useUsers({ page: 1, page_size: 100 });

  const [selectedEngineerId, setSelectedEngineerId] = useState<string>("");
  const [T_reported, setT_reported] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);

  // 仅筛选工程师角色用户
  const engineers = useMemo(() => {
    if (!usersData?.data) return [];
    return (usersData.data as any[]).filter((u) => u.role === "engineer");
  }, [usersData]);

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
      toast.success("指派成功");
      queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
      onOpenChange(false);
      // 重置表单
      setSelectedEngineerId("");
      setT_reported("");
    } catch (error: any) {
      toast.error(error.message || "指派失败");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>指派工程师</DialogTitle>
          <DialogDescription>
            选择工程师并填写 T报，跳过竞价流程直接指派
          </DialogDescription>
        </DialogHeader>

        {loadingUsers ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : engineers.length === 0 ? (
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
                    <th className="text-center px-3 py-2 font-medium">T报</th>
                  </tr>
                </thead>
                <tbody>
                  {engineers.map((eng: any) => {
                    const isSelected = selectedEngineerId === eng.id;
                    return (
                      <tr
                        key={eng.id}
                        className={`border-b last:border-0 ${isSelected ? "bg-muted/50" : ""}`}
                      >
                        <td className="px-3 py-2">
                          <RadioGroupItem value={eng.id} id={eng.id} />
                        </td>
                        <td className="px-3 py-2">
                          <Label htmlFor={eng.id} className="cursor-pointer">
                            {eng.full_name ?? eng.id.slice(0, 8)}
                          </Label>
                        </td>
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
                                setSelectedEngineerId(eng.id);
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
            disabled={!selectedEngineerId || submitting || loadingUsers}
          >
            {submitting ? "指派中..." : "确认指派"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
