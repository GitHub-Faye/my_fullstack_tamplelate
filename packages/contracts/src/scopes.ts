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
export type ScopeType = ItemScopeType | UserScopeType | SystemScopeType;

/**
 * 所有 Scope 列表
 */
export const ALL_SCOPES: ScopeType[] = [
  ...ALL_ITEM_SCOPES,
  ...ALL_USER_SCOPES,
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
