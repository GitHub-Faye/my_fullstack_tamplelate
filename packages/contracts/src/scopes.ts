/**
 * 权限 Scope 定义
 *
 * 与后端 apps/api/app/core/scopes.py 保持同步
 * 格式: "资源:操作"
 */

/**
 * Item 资源的权限 Scope
 */
export const ItemScope = {
  /** 读取 item 列表/详情 */
  READ: "item:read",
  /** 创建 item */
  CREATE: "item:create",
  /** 更新 item */
  UPDATE: "item:update",
  /** 删除 item */
  DELETE: "item:delete",
  /** 管理所有 item（包括他人的） */
  ADMIN: "item:admin",
} as const;

/**
 * Item Scope 类型
 */
export type ItemScopeType = typeof ItemScope[keyof typeof ItemScope];

/**
 * 所有 Item Scope 列表
 */
export const ALL_ITEM_SCOPES: ItemScopeType[] = [
  ItemScope.READ,
  ItemScope.CREATE,
  ItemScope.UPDATE,
  ItemScope.DELETE,
  ItemScope.ADMIN,
];

/**
 * 用户相关 Scope
 */
export const UserScope = {
  /** 读取用户信息 */
  READ: "user:read",
  /** 创建用户 */
  CREATE: "user:create",
  /** 更新用户信息 */
  UPDATE: "user:update",
  /** 删除用户 */
  DELETE: "user:delete",
  /** 管理所有用户 */
  ADMIN: "user:admin",
} as const;

/**
 * User Scope 类型
 */
export type UserScopeType = typeof UserScope[keyof typeof UserScope];

/**
 * 所有 User Scope 列表
 */
export const ALL_USER_SCOPES: UserScopeType[] = [
  UserScope.READ,
  UserScope.CREATE,
  UserScope.UPDATE,
  UserScope.DELETE,
  UserScope.ADMIN,
];

/**
 * 任务相关 Scope
 */
export const TaskScope = {
  /** 读取任务列表/详情 */
  READ: "task:read",
  /** 创建任务 */
  CREATE: "task:create",
  /** 更新任务 */
  UPDATE: "task:update",
  /** 删除任务 */
  DELETE: "task:delete",
  /** 管理所有任务 */
  ADMIN: "task:admin",
  /** 审核任务 */
  APPROVE: "task:approve",
  /** 转换任务类型 */
  CONVERT: "task:convert",
  /** 改派任务 */
  REASSIGN: "task:reassign",
} as const;

export type TaskScopeType = typeof TaskScope[keyof typeof TaskScope];

export const ALL_TASK_SCOPES: TaskScopeType[] = [
  TaskScope.READ,
  TaskScope.CREATE,
  TaskScope.UPDATE,
  TaskScope.DELETE,
  TaskScope.ADMIN,
  TaskScope.APPROVE,
  TaskScope.CONVERT,
  TaskScope.REASSIGN,
];

/**
 * 竞价相关 Scope
 */
export const BidScope = {
  /** 提交报价 */
  CREATE: "bid:create",
  /** 修改报价 */
  UPDATE: "bid:update",
  /** 查看报价列表 */
  READ: "bid:read",
} as const;

export type BidScopeType = typeof BidScope[keyof typeof BidScope];

export const ALL_BID_SCOPES: BidScopeType[] = [
  BidScope.CREATE,
  BidScope.UPDATE,
  BidScope.READ,
];

/**
 * 日报相关 Scope
 */
export const ReportScope = {
  /** 查看日报 */
  READ: "report:read",
  /** 填写日报 */
  CREATE: "report:create",
  /** 管理所有日报 */
  ADMIN: "report:admin",
} as const;

export type ReportScopeType = typeof ReportScope[keyof typeof ReportScope];

export const ALL_REPORT_SCOPES: ReportScopeType[] = [
  ReportScope.READ,
  ReportScope.CREATE,
  ReportScope.ADMIN,
];

/**
 * 星点相关 Scope
 */
export const StarPointScope = {
  /** 查看自己的星点 */
  READ: "starpoint:read",
  /** 管理星点 */
  ADMIN: "starpoint:admin",
} as const;

export type StarPointScopeType = typeof StarPointScope[keyof typeof StarPointScope];

export const ALL_STARPOINT_SCOPES: StarPointScopeType[] = [
  StarPointScope.READ,
  StarPointScope.ADMIN,
];

/**
 * 工资相关 Scope
 */
export const SalaryScope = {
  /** 查看自己的工资试算 */
  READ: "salary:read",
  /** 管理工资 */
  ADMIN: "salary:admin",
} as const;

export type SalaryScopeType = typeof SalaryScope[keyof typeof SalaryScope];

export const ALL_SALARY_SCOPES: SalaryScopeType[] = [
  SalaryScope.READ,
  SalaryScope.ADMIN,
];

/**
 * 客资相关 Scope
 */
export const ClientResourceScope = {
  /** 查看客资 */
  READ: "client-resource:read",
  /** 录入客资 */
  CREATE: "client-resource:create",
} as const;

export type ClientResourceScopeType = typeof ClientResourceScope[keyof typeof ClientResourceScope];

export const ALL_CLIENT_RESOURCE_SCOPES: ClientResourceScopeType[] = [
  ClientResourceScope.READ,
  ClientResourceScope.CREATE,
];

/**
 * 规则配置相关 Scope
 */
export const RuleScope = {
  /** 管理规则配置 */
  ADMIN: "rule:admin",
} as const;

export type RuleScopeType = typeof RuleScope[keyof typeof RuleScope];

export const ALL_RULE_SCOPES: RuleScopeType[] = [
  RuleScope.ADMIN,
];

/**
 * 系统管理 Scope
 */
export const SystemScope = {
  /** 系统只读访问 */
  READ: "system:read",
  /** 系统管理 */
  ADMIN: "system:admin",
} as const;

/**
 * System Scope 类型
 */
export type SystemScopeType = typeof SystemScope[keyof typeof SystemScope];

/**
 * 所有 Scope 的联合类型
 */
export type ScopeType =
  | ItemScopeType
  | UserScopeType
  | TaskScopeType
  | BidScopeType
  | ReportScopeType
  | StarPointScopeType
  | SalaryScopeType
  | ClientResourceScopeType
  | RuleScopeType
  | SystemScopeType;

/**
 * 所有 Scope 列表
 */
export const ALL_SCOPES: ScopeType[] = [
  ...ALL_ITEM_SCOPES,
  ...ALL_USER_SCOPES,
  ...ALL_TASK_SCOPES,
  ...ALL_BID_SCOPES,
  ...ALL_REPORT_SCOPES,
  ...ALL_STARPOINT_SCOPES,
  ...ALL_SALARY_SCOPES,
  ...ALL_CLIENT_RESOURCE_SCOPES,
  ...ALL_RULE_SCOPES,
  ...Object.values(SystemScope),
];

/**
 * 预定义角色对应的 Scopes
 */
export const DEFAULT_ROLE_SCOPES: Record<string, ScopeType[]> = {
  /** 只读用户 */
  viewer: [ItemScope.READ, UserScope.READ],

  /** 编辑者 */
  editor: [
    ItemScope.READ,
    ItemScope.CREATE,
    ItemScope.UPDATE,
    ItemScope.DELETE,
    UserScope.READ,
  ],

  /** 管理员 */
  admin: [
    ItemScope.READ,
    ItemScope.CREATE,
    ItemScope.UPDATE,
    ItemScope.DELETE,
    ItemScope.ADMIN,
    UserScope.READ,
    UserScope.CREATE,
    UserScope.UPDATE,
    UserScope.DELETE,
    UserScope.ADMIN,
    SystemScope.READ,
  ],

  /** 工程师 */
  engineer: [
    TaskScope.READ,
    BidScope.CREATE,
    BidScope.UPDATE,
    ReportScope.CREATE,
    ReportScope.READ,
    StarPointScope.READ,
    SalaryScope.READ,
  ],

  /** PM */
  pm: [
    TaskScope.READ,
    TaskScope.CREATE,
    TaskScope.UPDATE,
    ReportScope.READ,
    ClientResourceScope.READ,
    ClientResourceScope.CREATE,
    SalaryScope.READ,
  ],

  /** 管理员角色 */
  admin_role: [
    TaskScope.READ,
    TaskScope.CREATE,
    TaskScope.UPDATE,
    TaskScope.DELETE,
    TaskScope.ADMIN,
    TaskScope.APPROVE,
    TaskScope.CONVERT,
    TaskScope.REASSIGN,
    BidScope.READ,
    ReportScope.READ,
    ReportScope.ADMIN,
    StarPointScope.READ,
    StarPointScope.ADMIN,
    SalaryScope.READ,
    SalaryScope.ADMIN,
    ClientResourceScope.READ,
    UserScope.READ,
    UserScope.CREATE,
    UserScope.UPDATE,
    UserScope.DELETE,
    UserScope.ADMIN,
    RuleScope.ADMIN,
  ],

  /** 超级管理员 */
  superuser: [...ALL_SCOPES],
};

/**
 * 检查用户是否拥有指定 Scope
 */
export function hasScope(userScopes: ScopeType[], requiredScope: ScopeType): boolean {
  return userScopes.includes(requiredScope);
}

/**
 * 检查用户是否拥有任意一个指定 Scope
 */
export function hasAnyScope(userScopes: ScopeType[], requiredScopes: ScopeType[]): boolean {
  return requiredScopes.some((scope) => userScopes.includes(scope));
}

/**
 * 检查用户是否拥有所有指定 Scope
 */
export function hasAllScopes(userScopes: ScopeType[], requiredScopes: ScopeType[]): boolean {
  return requiredScopes.every((scope) => userScopes.includes(scope));
}

/**
 * 获取角色对应的 Scopes
 */
export function getRoleScopes(role: string): ScopeType[] {
  return DEFAULT_ROLE_SCOPES[role] || [];
}

/**
 * 验证 Scope 是否有效
 */
export function isValidScope(scope: string): scope is ScopeType {
  return ALL_SCOPES.includes(scope as ScopeType);
}
