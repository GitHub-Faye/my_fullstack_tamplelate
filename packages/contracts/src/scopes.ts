/**
 * 权限 Scope 定义
 *
 * 与后端 apps/api/app/core/scopes.py 保持同步（单一事实源的两个镜像，字符串必须逐字一致）
 * 格式: "资源:操作"
 */

/**
 * User 资源的权限 Scope
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
 * Role（角色）资源的专属权限 Scope
 */
export const RoleScope = {
  /** 读取角色列表/详情 */
  READ: "role:read",
  /** 创建角色 */
  CREATE: "role:create",
  /** 更新角色（名称 + scope 集合） */
  UPDATE: "role:update",
  /** 删除角色 */
  DELETE: "role:delete",
} as const;

/**
 * Role Scope 类型
 */
export type RoleScopeType = typeof RoleScope[keyof typeof RoleScope];

/**
 * 所有 Role Scope 列表
 */
export const ALL_ROLE_SCOPES: RoleScopeType[] = [
  RoleScope.READ,
  RoleScope.CREATE,
  RoleScope.UPDATE,
  RoleScope.DELETE,
];

/**
 * 所有 Scope 的联合类型
 */
export type ScopeType = UserScopeType | RoleScopeType;

/**
 * 所有 Scope 列表
 */
export const ALL_SCOPES: ScopeType[] = [
  ...ALL_USER_SCOPES,
  ...ALL_ROLE_SCOPES,
];

/**
 * 系统预置角色（不可修改/删除）
 */
export const BUILTIN_ROLES = ["viewer", "editor", "admin"] as const;

/**
 * 预定义角色对应的 Scopes
 * 与后端 app.core.database.init_roles_and_scopes 保持一致
 */
export const DEFAULT_ROLE_SCOPES: Record<string, ScopeType[]> = {
  /** 只读用户 */
  viewer: [UserScope.READ],

  /** 编辑者：用户读写 */
  editor: [
    UserScope.READ,
    UserScope.CREATE,
    UserScope.UPDATE,
    UserScope.DELETE,
  ],

  /** 管理员：所有用户权限 + 所有角色权限 */
  admin: [...ALL_USER_SCOPES, ...ALL_ROLE_SCOPES],
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
