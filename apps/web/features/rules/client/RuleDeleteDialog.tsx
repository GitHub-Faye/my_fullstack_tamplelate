"use client";

import { useState } from "react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Loader2, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { deleteRuleV1SystemRulesRuleIdDelete } from "@repo/sdk";
import type { SystemRulePublic } from "@repo/sdk";

interface RuleDeleteDialogProps {
  rule: SystemRulePublic | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

const CATEGORY_LABELS: Record<string, string> = {
  starpoint_reward: "星点奖励",
  salary_formula: "工资公式",
  completion_judgment: "完成判定",
  system_param: "系统参数",
};

export function RuleDeleteDialog({
  rule,
  open,
  onOpenChange,
  onSuccess,
}: RuleDeleteDialogProps) {
  const [submitting, setSubmitting] = useState(false);

  const handleDelete = async () => {
    if (!rule) return;
    setSubmitting(true);
    try {
      await deleteRuleV1SystemRulesRuleIdDelete({
        path: { rule_id: rule.id },
        throwOnError: true,
      });
      toast.success("规则已删除");
      onSuccess();
      onOpenChange(false);
    } catch (error: any) {
      toast.error(error.message || "删除失败");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>确认删除</AlertDialogTitle>
          <AlertDialogDescription>
            确定要删除规则
            <span className="font-medium"> {rule?.name} </span>
            （{CATEGORY_LABELS[rule?.category ?? ""] || rule?.category}）吗？
            <br />
            此操作不可撤销。
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={submitting}>取消</AlertDialogCancel>
          <AlertDialogAction
            onClick={(e) => {
              e.preventDefault();
              handleDelete();
            }}
            disabled={submitting}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {submitting ? (
              <>
                <Loader2 className="mr-1 h-4 w-4 animate-spin" />
                删除中...
              </>
            ) : (
              <>
                <Trash2 className="mr-1 h-4 w-4" />
                确认删除
              </>
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}