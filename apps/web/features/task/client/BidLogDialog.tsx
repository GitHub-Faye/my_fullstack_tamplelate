"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Loader2 } from "lucide-react";
import { readBidsByTaskV1TasksTaskIdBidsGet, type TaskPublic, type BidPublic } from "@repo/sdk";
import { formatDateTime } from "@/lib/utils";

/**
 * 报价记录弹窗
 *
 * 查看指定任务的工程师报价列表
 */
export function BidLogDialog({
  task,
  open,
  onOpenChange,
}: {
  task: TaskPublic;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [bids, setBids] = useState<BidPublic[] | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open && task) {
      setLoading(true);
      readBidsByTaskV1TasksTaskIdBidsGet({ path: { task_id: task.id } })
        .then((res) => setBids(res.data?.data ?? []))
        .catch(() => setBids([]))
        .finally(() => setLoading(false));
    }
  }, [open, task]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>报价记录 - {task.name}</DialogTitle>
          <DialogDescription>查看该任务的工程师报价列表</DialogDescription>
        </DialogHeader>
        {loading ? (
          <div className="flex justify-center py-8"><Loader2 className="h-6 w-6 animate-spin" /></div>
        ) : bids && bids.length > 0 ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-muted-foreground">
                <th className="text-left px-3 py-2 font-medium">工程师</th>
                <th className="text-left px-3 py-2 font-medium">报价工时(T报)</th>
                <th className="text-left px-3 py-2 font-medium">报价金额</th>
                <th className="text-left px-3 py-2 font-medium">报价时间</th>
              </tr>
            </thead>
            <tbody>
              {bids.map((bid) => (
                <tr key={bid.id} className="border-b last:border-0">
                  <td className="px-3 py-2">{bid.engineer_id?.slice(0, 8) ?? "-"}</td>
                  <td className="px-3 py-2">{bid.T_reported != null ? `${bid.T_reported}h` : "-"}</td>
                  <td className="px-3 py-2">¥{bid.amount?.toLocaleString() ?? "-"}</td>
                  <td className="px-3 py-2 text-muted-foreground">{formatDateTime(bid.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-center py-8 text-muted-foreground">暂无报价记录</p>
        )}
      </DialogContent>
    </Dialog>
  );
}