"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { updateRuleV1SystemRulesRuleIdPut } from "@repo/sdk";
import type { SystemRulePublic, SystemRuleUpdate } from "@repo/sdk";

const CATEGORY_LABELS: Record<string, string> = {
  starpoint_reward: "星点奖励",
  salary_formula: "工资公式",
  completion_judgment: "完成判定",
  system_param: "系统参数",
};

interface RuleEditDialogProps {
  rule: SystemRulePublic | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

// 提取 JSON key 列表，用于显示字段提示
function getJsonKeys(raw: string): string[] {
  try {
    const parsed = JSON.parse(raw);
    return Object.keys(parsed);
  } catch {
    return [];
  }
}

// 将 JSON 值按 key 分行展示，方便用户只改值
function formatValueForEdit(raw: string): string {
  try {
    const parsed = JSON.parse(raw);
    const lines: string[] = [];
    for (const [key, val] of Object.entries(parsed)) {
      lines.push(`"${key}": ${JSON.stringify(val)}`);
    }
    return lines.join(",\n");
  } catch {
    return raw;
  }
}

// 将编辑后的行文本还原为 JSON
function parseLinesToJson(raw: string, originalKeys: string[]): string {
  // 尝试直接 JSON.parse
  try {
    JSON.parse(raw);
    return raw;
  } catch {
    // 忽略
  }
  // 按行解析 key: value 格式
  const result: Record<string, any> = {};
  const lines = raw.split("\n");
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    // 匹配 "key": value 或 key: value
    const colonIdx = trimmed.indexOf(":");
    if (colonIdx === -1) continue;
    const keyRaw = trimmed.slice(0, colonIdx).trim().replace(/^"|"$/g, "");
    let valStr = trimmed.slice(colonIdx + 1).trim();
    // 去掉尾部的逗号
    if (valStr.endsWith(",")) valStr = valStr.slice(0, -1).trim();
    if (!keyRaw) continue;
    try {
      result[keyRaw] = JSON.parse(valStr);
    } catch {
      // 尝试作为字符串
      result[keyRaw] = valStr.replace(/^"|"$/g, "");
    }
  }
  // 如果解析出了内容就返回
  if (Object.keys(result).length > 0) {
    return JSON.stringify(result);
  }
  return raw;
}

export function RuleEditDialog({
  rule,
  open,
  onOpenChange,
  onSuccess,
}: RuleEditDialogProps) {
  const [value, setValue] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // 当 rule 变化时同步（open 或 rule 变化时重置）
  useEffect(() => {
    if (rule && open) {
      setValue(formatValueForEdit(rule.value));
      setSubmitting(false);
    }
  }, [rule?.id, open]);

  const handleSubmit = async () => {
    if (!rule) return;
    if (!value.trim()) {
      toast.error("规则值不能为空");
      return;
    }

    const originalKeys = getJsonKeys(rule.value);
    const finalValue = parseLinesToJson(value.trim(), originalKeys);

    setSubmitting(true);
    try {
      const body: SystemRuleUpdate = {
        value: finalValue,
      };
      await updateRuleV1SystemRulesRuleIdPut({
        path: { rule_id: rule.id },
        body,
        throwOnError: true,
      });
      toast.success("规则已更新");
      onSuccess();
      onOpenChange(false);
    } catch (error: any) {
      toast.error(error.message || "更新失败");
    } finally {
      setSubmitting(false);
    }
  };

  const jsonFields = (rule ? getJsonKeys(rule.value) : []) as string[];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>编辑规则</DialogTitle>
          <DialogDescription>
            {CATEGORY_LABELS[rule?.category ?? ""] || rule?.category}
            {" / "}
            <span className="font-medium">{rule?.name}</span>
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* 规则名称 — 只读展示 */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right">规则名称</Label>
            <div className="col-span-3 text-sm py-2 text-muted-foreground">
              {rule?.name}
            </div>
          </div>

          {/* 规则值 — 仅编辑值 */}
          <div className="grid grid-cols-4 items-start gap-4">
            <Label className="text-right pt-2">规则值</Label>
            <div className="col-span-3 space-y-2">
              <Textarea
                className="font-mono text-sm min-h-[120px]"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder="修改值即可"
              />
              {jsonFields.length > 0 && (
                <p className="text-xs text-muted-foreground">
                  可修改字段：{jsonFields.join("、")}
                </p>
              )}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={submitting}
          >
            取消
          </Button>
          <Button onClick={handleSubmit} disabled={submitting}>
            {submitting ? (
              <>
                <Loader2 className="mr-1 h-4 w-4 animate-spin" />
                保存中...
              </>
            ) : (
              "保存"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}