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
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { updateSalaryParamsV1SalariesUsersUserIdParamsPut } from "@repo/sdk";

interface EngineerSalaryRow {
  user_id: string;
  full_name?: string | null;
  role: string;
  S0?: number | null;
  H0?: number | null;
  T_monthly_plan?: number | null;
  T_effective?: number | null;
  T_actual_monthly?: number | null;
  T_reported_monthly?: number | null;
  P_diff?: number | null;
  k_coefficient?: number | null;
  current_starpoint?: number | null;
  salary_final?: number | null;
}

interface PMSalaryRow {
  user_id: string;
  full_name?: string | null;
  role: string;
  S_base?: number | null;
  S_assess?: number | null;
  R_base?: number | null;
  R_assess?: number | null;
  salary_total?: number | null;
}

type SalaryUser = EngineerSalaryRow | PMSalaryRow;

interface SalaryEditDialogProps {
  user: SalaryUser | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function SalaryEditDialog({
  user,
  open,
  onOpenChange,
  onSuccess,
}: SalaryEditDialogProps) {
  if (!user) return null;

  const isEngineer = user.role === "engineer";
  const [S0, setS0] = useState<string>(
    isEngineer ? String((user as EngineerSalaryRow).S0 ?? "") : ""
  );
  const [T_monthly_plan, setT_monthly_plan] = useState<string>(
    isEngineer ? String((user as EngineerSalaryRow).T_monthly_plan ?? "") : ""
  );
  const [S_base, setS_base] = useState<string>(
    !isEngineer ? String((user as PMSalaryRow).S_base ?? "") : ""
  );
  const [S_assess, setS_assess] = useState<string>(
    !isEngineer ? String((user as PMSalaryRow).S_assess ?? "") : ""
  );
  const [R_base, setR_base] = useState<string>(
    !isEngineer ? String((user as PMSalaryRow).R_base ?? "") : ""
  );
  const [R_assess, setR_assess] = useState<string>(
    !isEngineer ? String((user as PMSalaryRow).R_assess ?? "") : ""
  );
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    const body: Record<string, number> = {};

    if (isEngineer) {
      const s0 = parseFloat(S0);
      if (isNaN(s0) || s0 < 0) {
        toast.error("S0 必须 >= 0");
        return;
      }
      body.S0 = s0;

      if (T_monthly_plan !== "") {
        const tmp = parseFloat(T_monthly_plan);
        if (isNaN(tmp) || tmp < 0) {
          toast.error("T月计划必须 >= 0");
          return;
        }
        body.T_monthly_plan = tmp;
      }
    } else {
      const sBase = parseFloat(S_base);
      if (isNaN(sBase) || sBase < 0) {
        toast.error("S底 必须 >= 0");
        return;
      }
      body.S_base = sBase;

      const sAssess = parseFloat(S_assess);
      if (isNaN(sAssess) || sAssess < 0) {
        toast.error("S考 必须 >= 0");
        return;
      }
      body.S_assess = sAssess;

      if (R_base !== "") {
        const rBase = parseFloat(R_base);
        if (isNaN(rBase) || rBase < 0 || rBase > 1) {
          toast.error("R底 必须在 0~1 之间");
          return;
        }
        body.R_base = rBase;
      }

      if (R_assess !== "") {
        const rAssess = parseFloat(R_assess);
        if (isNaN(rAssess) || rAssess < 0 || rAssess > 1) {
          toast.error("R考 必须在 0~1 之间");
          return;
        }
        body.R_assess = rAssess;
      }
    }

    setSubmitting(true);
    try {
      await updateSalaryParamsV1SalariesUsersUserIdParamsPut({
        path: { user_id: user.user_id },
        body,
        throwOnError: true,
      });
      toast.success("工资参数已更新");
      onSuccess();
      onOpenChange(false);
    } catch (error: any) {
      toast.error(error.message || "更新失败");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>编辑工资参数</DialogTitle>
          <DialogDescription>
            {user.full_name || user.user_id} - {isEngineer ? "工程师" : "市场产品PM"}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {isEngineer ? (
            <>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="S0" className="text-right">
                  S0
                </Label>
                <Input
                  id="S0"
                  type="number"
                  step="0.01"
                  min="0"
                  className="col-span-3"
                  value={S0}
                  onChange={(e) => setS0(e.target.value)}
                  placeholder="月度工资基数"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="T_monthly_plan" className="text-right">
                  T月计划
                </Label>
                <Input
                  id="T_monthly_plan"
                  type="number"
                  step="0.1"
                  min="0"
                  className="col-span-3"
                  value={T_monthly_plan}
                  onChange={(e) => setT_monthly_plan(e.target.value)}
                  placeholder="月计划工时"
                />
              </div>
              <p className="text-xs text-muted-foreground ml-[25%]">
                H0 由系统自动计算（S0 ÷ T月计划）
              </p>
            </>
          ) : (
            <>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="S_base" className="text-right">
                  S底
                </Label>
                <Input
                  id="S_base"
                  type="number"
                  step="0.01"
                  min="0"
                  className="col-span-3"
                  value={S_base}
                  onChange={(e) => setS_base(e.target.value)}
                  placeholder="底薪"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="S_assess" className="text-right">
                  S考
                </Label>
                <Input
                  id="S_assess"
                  type="number"
                  step="0.01"
                  min="0"
                  className="col-span-3"
                  value={S_assess}
                  onChange={(e) => setS_assess(e.target.value)}
                  placeholder="考核部分"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="R_base" className="text-right">
                  R底
                </Label>
                <Input
                  id="R_base"
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  className="col-span-3"
                  value={R_base}
                  onChange={(e) => setR_base(e.target.value)}
                  placeholder="底薪比例 (0~1)"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="R_assess" className="text-right">
                  R考
                </Label>
                <Input
                  id="R_assess"
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  className="col-span-3"
                  value={R_assess}
                  onChange={(e) => setR_assess(e.target.value)}
                  placeholder="考核比例 (0~1)"
                />
              </div>
            </>
          )}
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