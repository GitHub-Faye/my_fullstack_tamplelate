"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Search, Plus } from "lucide-react";

export default function AdminRulesPage() {
  const [category, setCategory] = useState("all");

  const rules = [
    { category: "星点奖励", name: "T实小于等于T报", value: "按提前/准时完成加星点", role: "工程师" },
    { category: "工资公式", name: "工程师收入试算", value: "S下 = (S0 - P差额) × K", role: "工程师" },
    { category: "PM客资", name: "本月新增客资", value: "期末公司客资量 - 月初公司客资存量", role: "市场产品PM" },
    { category: "完成判定", name: "提前完成", value: "T实 ≤ 0.8×T报，星点 +5", role: "工程师" },
    { category: "完成判定", name: "按时完成", value: "T实 ≤ T报，星点 +3", role: "工程师" },
    { category: "完成判定", name: "超时≤20%", value: "T实 ≤ 1.2×T报，星点 -5", role: "工程师" },
    { category: "完成判定", name: "超时21-50%", value: "T实 ≤ 1.5×T报，星点 -10", role: "工程师" },
    { category: "完成判定", name: "超时51-100%", value: "T实 ≤ 2×T报，星点 -20", role: "工程师" },
    { category: "完成判定", name: "超时>100%", value: "T实 > 2×T报，星点 -30", role: "工程师" },
  ];

  const filteredRules = category === "all" ? rules : rules.filter((r) => r.category === category);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">规则配置</h1>
        <p className="text-muted-foreground">管理系统中的业务规则</p>
      </div>
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4 flex-wrap">
            <Button variant="default" size="sm" disabled><Plus className="mr-1 h-4 w-4" />新增规则</Button>
            <div className="flex items-center gap-2">
              <label className="text-sm">分类</label>
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger className="w-[160px]"><SelectValue placeholder="全部" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部</SelectItem>
                  <SelectItem value="星点奖励">星点奖励</SelectItem>
                  <SelectItem value="工资公式">工资公式</SelectItem>
                  <SelectItem value="PM客资">PM客资</SelectItem>
                  <SelectItem value="完成判定">完成判定</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button variant="outline" size="sm" disabled><Search className="mr-1 h-4 w-4" />搜索</Button>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle>规则配置</CardTitle></CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-muted-foreground">
                  <th className="text-left py-3 px-4">分类</th>
                  <th className="text-left py-3 px-4">规则名称</th>
                  <th className="text-left py-3 px-4">规则值/公式</th>
                  <th className="text-left py-3 px-4">适用角色</th>
                  <th className="text-right py-3 px-4">操作</th>
                </tr>
              </thead>
              <tbody>
                {filteredRules.map((rule, i) => (
                  <tr key={i} className="border-b last:border-0">
                    <td className="py-3 px-4">{rule.category}</td>
                    <td className="py-3 px-4 font-medium">{rule.name}</td>
                    <td className="py-3 px-4 text-muted-foreground">{rule.value}</td>
                    <td className="py-3 px-4">{rule.role}</td>
                    <td className="py-3 px-4 text-right"><Button variant="link" size="sm" disabled>修改</Button></td>
                  </tr>
                ))}
                {filteredRules.length === 0 && (
                  <tr><td colSpan={5} className="text-center py-8 text-muted-foreground">暂无规则数据</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}