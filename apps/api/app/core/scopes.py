"""
权限范围（Scope）定义模块

定义系统中所有的权限范围常量，用于 RBAC 权限控制。
格式遵循 "资源:操作" 的命名规范。
"""

from enum import Enum


class UserScope(str, Enum):
    """User 资源的权限范围"""

    READ = "user:read"       # 读取用户信息
    CREATE = "user:create"  # 创建用户
    UPDATE = "user:update"  # 更新用户
    DELETE = "user:delete"  # 删除用户
    ADMIN = "user:admin"    # 管理所有用户


class SystemScope(str, Enum):
    """系统管理权限范围"""

    READ = "system:read"    # 系统只读访问
    ADMIN = "system:admin"  # 系统管理


# 所有 scope 的集合（用于初始化或验证）
ALL_USER_SCOPES = [
    UserScope.READ,
    UserScope.CREATE,
    UserScope.UPDATE,
    UserScope.DELETE,
    UserScope.ADMIN,
]

ALL_SYSTEM_SCOPES = [
    SystemScope.READ,
    SystemScope.ADMIN,
]

ALL_SCOPES = ALL_USER_SCOPES + ALL_SYSTEM_SCOPES


# 预定义角色对应的 scopes
# 注意：与 packages/contracts/src/scopes.ts 的 DEFAULT_ROLE_SCOPES 保持同步
# 系统预置角色（viewer/editor/admin）不可修改/删除，
# 由 app.core.database.init_roles_and_scopes 在启动时初始化。
DEFAULT_ROLE_SCOPES = {
    "viewer": [
        UserScope.READ,
    ],
    "editor": [
        UserScope.READ,
        UserScope.CREATE,
        UserScope.UPDATE,
        UserScope.DELETE,
    ],
    "admin": [
        UserScope.READ,
        UserScope.CREATE,
        UserScope.UPDATE,
        UserScope.DELETE,
        UserScope.ADMIN,
        SystemScope.READ,
    ],
}
