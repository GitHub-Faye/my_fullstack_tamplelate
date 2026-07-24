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
import { Loader2 } from "lucide-react";
import { readMySalaryV1SalariesMyGet } from "@repo/sdk";
import type { PmSalaryDetail } from "@repo/sdk";

/**
 * PM 收入试算明细弹窗
 *
 * 从 GET /v1/salaries/my 获取工资试算详情，展示 S底、S考 等字段
 */
export function PmSalaryDetailDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [data, setData] = useState<PmSalaryDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 弹窗打开时加载数据
  useEffect(() => {
    if (open && !data && !loading) {
      setLoading(true);
      setError(null);
      readMySalaryV1SalariesMyGet()
        .then((res) => {
          setData(res.data as PmSalaryDetail);
        })
        .catch((err) => {
          setError(err instanceof Error ? err.message : "加载失败");
        })
        .finally(() => setLoading(false));
    }
  }, [open]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>收入试算明细</DialogTitle>
          <DialogDescription>本月工资试算详情</DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : error ? (
          <div className="text-center py-8 text-red-500 text-sm">{error}</div>
        ) : data ? (
          <div className="space-y-3">
            {/* 用户信息 */}
            <div className="text-sm text-muted-foreground">
              {data.full_name && <span>{data.full_name} · </span>}
              <span>{data.role === "pm" ? "市场产品PM" : data.role}</span>
            </div>

            <div className="divide-y">
              <Row label="S底（底薪）" value={data.S_base} />
              <Row label="S考（考核部分）" value={data.S_assess} />
              {data.R_base != null && (
                <Row label="R底（底薪比例）" value={`${(data.R_base * 100).toFixed(0)}%`} />
              )}
              {data.R_assess != null && (
                <Row label="R考（考核比例）" value={`${(data.R_assess * 100).toFixed(0)}%`} />
              )}
            </div>

            <div className="border-t pt-3 mt-3">
              <Row label="S总（总工资）" value={`¥${data.salary_total.toLocaleString()}`} bold />
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground text-sm">
            暂无数据
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

function Row({
  label,
  value,
  bold,
}: {
  label: string;
  value: string | number;
  bold?: boolean;
}) {
  return (
    <div className="flex justify-between py-2 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className={bold ? "font-bold text-base" : ""}>{value}</span>
    </div>
  );
}