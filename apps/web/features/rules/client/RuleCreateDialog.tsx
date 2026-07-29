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
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { createRuleV1SystemRulesPost } from "@repo/sdk";
import type { SystemRuleCreate, RuleCategory } from "@repo/sdk";

const CATEGORIES = [
  { value: "starpoint_reward", label: "星点奖励" },
  { value: "salary_formula", label: "工资公式" },
  { value: "completion_judgment", label: "完成判定" },
  { value: "system_param", label: "系统参数" },
];

interface RuleCreateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function RuleCreateDialog({
  open,
  onOpenChange,
  onSuccess,
}: RuleCreateDialogProps) {
  const [category, setCategory] = useState("");
  const [name, setName] = useState("");
  const [value, setValue] = useState("");
  const [appliesTo, setAppliesTo] = useState("");
  const [isActive, setIsActive] = useState(true);
  const [isPublic, setIsPublic] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!category) {
      toast.error("请选择规则分类");
      return;
    }
    if (!name.trim()) {
      toast.error("规则名称不能为空");
      return;
    }
    if (!value.trim()) {
      toast.error("规则值不能为空");
      return;
    }

    setSubmitting(true);
    try {
      const body: SystemRuleCreate = {
        category: category as RuleCategory,
        name: name.trim(),
        value: value.trim(),
        applies_to: appliesTo.trim() || null,
        is_active: isActive,
        is_public: isPublic,
      };
      await createRuleV1SystemRulesPost({
        body,
        throwOnError: true,
      });
      toast.success("规则已创建");
      onSuccess();
      onOpenChange(false);
      // 重置表单
      setCategory("");
      setName("");
      setValue("");
      setAppliesTo("");
      setIsActive(true);
      setIsPublic(false);
    } catch (error: any) {
      toast.error(error.message || "创建失败");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>新增规则</DialogTitle>
          <DialogDescription>创建新的业务规则配置</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="create-category" className="text-right">
              规则分类
            </Label>
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger className="col-span-3">
                <SelectValue placeholder="请选择分类" />
              </SelectTrigger>
              <SelectContent>
                {CATEGORIES.map((c) => (
                  <SelectItem key={c.value} value={c.value}>
                    {c.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="create-name" className="text-right">
              规则名称
            </Label>
            <Input
              id="create-name"
              className="col-span-3"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="规则名称"
            />
          </div>
          <div className="grid grid-cols-4 items-start gap-4">
            <Label htmlFor="create-value" className="text-right pt-2">
              规则值/公式
            </Label>
            <Textarea
              id="create-value"
              className="col-span-3 font-mono text-sm min-h-[100px]"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder='JSON 格式或数值，例如：{"min_salary": 5000, "top_k": 1.2}'
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="create-applies-to" className="text-right">
              适用角色
            </Label>
            <Input
              id="create-applies-to"
              className="col-span-3"
              value={appliesTo}
              onChange={(e) => setAppliesTo(e.target.value)}
              placeholder="engineer / pm / 留空表示全部"
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right">状态</Label>
            <div className="col-span-3 flex items-center gap-6">
              <div className="flex items-center gap-2">
                <Checkbox
                  id="create-is-active"
                  checked={isActive}
                  onCheckedChange={(v) => setIsActive(v === true)}
                />
                <Label htmlFor="create-is-active" className="cursor-pointer">
                  启用
                </Label>
              </div>
              <div className="flex items-center gap-2">
                <Checkbox
                  id="create-is-public"
                  checked={isPublic}
                  onCheckedChange={(v) => setIsPublic(v === true)}
                />
                <Label htmlFor="create-is-public" className="cursor-pointer">
                  对员工公开
                </Label>
              </div>
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
                创建中...
              </>
            ) : (
              "创建"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}