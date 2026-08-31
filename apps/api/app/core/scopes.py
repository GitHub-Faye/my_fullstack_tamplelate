"""
权限范围（Scope）定义模块

定义系统中所有的权限范围常量，用于 RBAC 权限控制。
格式遵循 "资源:操作" 的命名规范。

scope 资源分类：
- user:*   → 用户资源的操作权限（用户管理）
- role:*   → 角色资源的操作权限（角色管理，专属权限）

注意：角色管理使用专属的 role:* scope，而不是复用 user:*，
因为角色 / scope 属于系统级配置资源，不是用户数据。
"""

from enum import Enum


class UserScope(str, Enum):
    """User 资源的权限范围"""

    READ = "user:read"       # 读取用户信息
    CREATE = "user:create"  # 创建用户
    UPDATE = "user:update"  # 更新用户
    DELETE = "user:delete"  # 删除用户
    ADMIN = "user:admin"    # 管理所有用户


class RoleScope(str, Enum):
    """Role（角色）资源的专属权限范围"""

    READ = "role:read"       # 读取角色列表/详情
    CREATE = "role:create"  # 创建角色
    UPDATE = "role:update"  # 更新角色（名称 + scope 集合）
    DELETE = "role:delete"  # 删除角色


# 所有 scope 的集合（用于初始化或验证）
ALL_USER_SCOPES = [
    UserScope.READ,
    UserScope.CREATE,
    UserScope.UPDATE,
    UserScope.DELETE,
    UserScope.ADMIN,
]

ALL_ROLE_SCOPES = [
    RoleScope.READ,
    RoleScope.CREATE,
    RoleScope.UPDATE,
    RoleScope.DELETE,
]

ALL_SCOPES = ALL_USER_SCOPES + ALL_ROLE_SCOPES

# 系统预置角色不可修改或删除。
BUILTIN_ROLES = ("viewer", "editor", "admin")


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
        *ALL_USER_SCOPES,
        *ALL_ROLE_SCOPES,
    ],
}