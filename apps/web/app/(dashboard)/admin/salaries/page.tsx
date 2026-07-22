"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Search, Download } from "lucide-react";

export default function AdminSalariesPage() {
  const [month] = useState("2026-06");
  const [person] = useState("all");
  const [tab, setTab] = useState<"engineer" | "pm">("engineer");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">工资管理</h1>
        <p className="text-muted-foreground">查看和管理员工工资</p>
      </div>
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <label className="text-sm">月份</label>
              <Input type="month" className="w-[160px]" value={month} disabled />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-sm">人员</label>
              <Select value={person} disabled>
                <SelectTrigger className="w-[130px]"><SelectValue placeholder="全部" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部</SelectItem>
                  <SelectItem value="engineer">工程师</SelectItem>
                  <SelectItem value="pm">市场产品PM</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button variant="outline" size="sm" disabled><Search className="mr-1 h-4 w-4" />搜索</Button>
            <Button variant="default" size="sm" disabled><Download className="mr-1 h-4 w-4" />导出工资表</Button>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <CardTitle>工资管理</CardTitle>
            <div className="flex gap-1 bg-muted rounded-lg p-1">
              <button className={`px-3 py-1 text-sm rounded-md transition-colors ${tab === "engineer" ? "bg-background shadow-sm" : "hover:bg-background/50"}`} onClick={() => setTab("engineer")}>工程师</button>
              <button className={`px-3 py-1 text-sm rounded-md transition-colors ${tab === "pm" ? "bg-background shadow-sm" : "hover:bg-background/50"}`} onClick={() => setTab("pm")}>市场产品PM</button>
            </div>
          </div>
        </CardHeader>
        <CardContent><p className="text-sm text-muted-foreground">工资数据将在后续版本中接入实际 API 后展示</p></CardContent>
      </Card>
    </div>
  );
}