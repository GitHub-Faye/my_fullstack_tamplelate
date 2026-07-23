/**
 * Task 业务契约
 *
 * 与后端 apps/api/app/core/models.py 保持同步
 * 包含任务状态、类型枚举和表单验证 Schema
 */

// ==================== 任务状态枚举 ====================

/**
 * 任务状态
 *
 * 状态流转：
 * unconfirmed -> bidding -> pending_start -> in_progress -> completed
 * 中间状态：paused（可从 in_progress 暂停）
 */
export const TaskStatus = {
  UNCONFIRMED: "unconfirmed",
  BIDDING: "bidding",
  PENDING_START: "pending_start",
  IN_PROGRESS: "in_progress",
  PAUSE_REQUESTED: "pause_requested",
  PAUSED: "paused",
  COMPLETED: "completed",
} as const;

export type TaskStatusType = typeof TaskStatus[keyof typeof TaskStatus];

/**
 * TaskStatus 的中文标签映射
 */
export const TASK_STATUS_LABELS: Record<TaskStatusType, string> = {
  [TaskStatus.UNCONFIRMED]: "未确认",
  [TaskStatus.BIDDING]: "竞价中",
  [TaskStatus.PENDING_START]: "待启动",
  [TaskStatus.IN_PROGRESS]: "进行中",
  [TaskStatus.PAUSE_REQUESTED]: "暂停待审批",
  [TaskStatus.PAUSED]: "暂停中",
  [TaskStatus.COMPLETED]: "已完成",
};

/**
 * TaskStatus 对应的样式/颜色映射
 */
export const TASK_STATUS_COLORS: Record<TaskStatusType, string> = {
  [TaskStatus.UNCONFIRMED]: "gray",
  [TaskStatus.BIDDING]: "orange",
  [TaskStatus.PENDING_START]: "orange",
  [TaskStatus.IN_PROGRESS]: "blue",
  [TaskStatus.PAUSE_REQUESTED]: "orange",
  [TaskStatus.PAUSED]: "orange",
  [TaskStatus.COMPLETED]: "green",
};

// ==================== 任务类型枚举 ====================

export const TaskType = {
  NORMAL: "normal",
  URGENT: "urgent",
  CONVENIENT: "convenient",
} as const;

export type TaskTypeType = typeof TaskType[keyof typeof TaskType];

export const TASK_TYPE_LABELS: Record<TaskTypeType, string> = {
  [TaskType.NORMAL]: "正常任务",
  [TaskType.URGENT]: "紧急任务",
  [TaskType.CONVENIENT]: "便捷任务",
};

export const TASK_TYPE_COLORS: Record<TaskTypeType, string> = {
  [TaskType.NORMAL]: "blue",
  [TaskType.URGENT]: "red",
  [TaskType.CONVENIENT]: "green",
};

// ==================== 表单验证 Schema ====================

/**
 * 任务创建表单验证
 */
export const taskCreateSchema = {
  name: {
    required: true,
    minLength: 1,
    maxLength: 255,
    message: "任务名称不能为空",
  },
  description: {
    maxLength: 2000,
    message: "任务描述不能超过2000个字符",
  },
  task_type: {
    required: false,
    message: "请选择任务类型",
  },
} as const;

/**
 * 任务更新表单验证
 */
export const taskUpdateSchema = {
  name: {
    minLength: 1,
    maxLength: 255,
    message: "任务名称最多255个字符",
  },
  description: {
    maxLength: 2000,
    message: "任务描述不能超过2000个字符",
  },
} as const;

// ==================== 可编辑状态 ====================

/**
 * PM 可编辑任务的状态列表
 * 只有这些状态下的任务 PM 可以编辑/删除
 */
export const PM_EDITABLE_STATUSES: TaskStatusType[] = [
  TaskStatus.UNCONFIRMED,
  TaskStatus.BIDDING,
];

/**
 * 可删除任务的状态列表
 */
export const DELETABLE_STATUSES: TaskStatusType[] = [
  TaskStatus.UNCONFIRMED,
];