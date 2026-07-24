/** 操作类型选项：供筛选下拉和表格显示共用 */
export const ACTION_OPTIONS = [
  { value: "task.create", label: "发布任务" },
  { value: "task.approve", label: "审核通过" },
  { value: "task.publish", label: "发布任务" },
  { value: "task.convert_type", label: "转换类型" },
  { value: "task.reassign", label: "改派任务" },
  { value: "task.pause_approve", label: "批准暂停" },
  { value: "task.pause_reject", label: "驳回暂停" },
  { value: "user.create", label: "创建用户" },
  { value: "user.toggle_active", label: "启用/禁用用户" },
  { value: "salary.update", label: "更新工资参数" },
  { value: "system_rule.update", label: "更新规则" },
] as const;

/** 操作类型标签映射：key = action value, value = 显示文字 */
export const ACTION_LABELS: Record<string, string> = Object.fromEntries(
  ACTION_OPTIONS.map((opt) => [opt.value, opt.label]),
);