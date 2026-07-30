"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { adjustStarpointV1StarpointsAdjustPost } from "@repo/sdk";
import type { TaskPublic } from "@repo/sdk";

/**
 * 星点评分弹窗
 *
 * PM 对已完成任务进行评价，输入加分或扣分的星点值及原因。
 * 调用 /v1/starpoints/adjust 接口对负责该任务的工程师进行星点调整。
 */
export function StarPointReviewDialog({
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
  const [changeAmount, setChangeAmount] = useState("");
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    const amount = parseInt(changeAmount, 10);
    if (isNaN(amount) || amount === 0) {
      toast.error("请输入有效的星点值（正数加分，负数扣减）");
      return;
    }
    if (!reason.trim()) {
      toast.error("请填写评价原因");
      return;
    }

    setSubmitting(true);
    try {
      await adjustStarpointV1StarpointsAdjustPost({
        throwOnError: true,
        body: {
          engineer_id: task.engineer_id!,
          change_amount: amount,
          reason: reason.trim(),
        },
      });
      toast.success(`星点${amount > 0 ? "+" : ""}${amount} 评价成功`);
      setChangeAmount("");
      setReason("");
      onSuccess?.();
      onOpenChange(false);
    } catch (err: any) {
      toast.error(err.message || "评价失败");
    } finally {
      setSubmitting(false);
    }
  };

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      setChangeAmount("");
      setReason("");
    }
    onOpenChange(open);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[420px]">
        <DialogHeader>
          <DialogTitle>星点评分</DialogTitle>
          <DialogDescription>
            对任务「{task.name}」的工程师表现进行评价
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="text-sm text-muted-foreground">
            工程师：{(task as any).engineer_name ?? task.engineer_id?.slice(0, 8) ?? "-"}
          </div>

          <div className="space-y-2">
            <Label htmlFor="change-amount">
              星点变化 <span className="text-xs text-muted-foreground">（正数加分，负数扣减）</span>
            </Label>
            <Input
              id="change-amount"
              type="number"
              placeholder="例如：10 或 -5"
              value={changeAmount}
              onChange={(e) => setChangeAmount(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="reason">评价原因</Label>
            <Textarea
              id="reason"
              placeholder="请填写评价原因"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit} disabled={submitting}>
            {submitting ? "提交中..." : "提交评价"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}