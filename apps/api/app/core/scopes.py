"""
权限范围（Scope）定义模块

定义系统中所有的权限范围常量，用于 RBAC 权限控制。
格式遵循 "资源:操作" 的命名规范。
"""

from enum import Enum


class ItemScope(str, Enum):
    """Item 资源的权限范围"""

    READ = "item:read"       # 读取 item 列表/详情
    CREATE = "item:create"  # 创建 item
    UPDATE = "item:update"  # 更新 item
    DELETE = "item:delete"  # 删除 item
    ADMIN = "item:admin"    # 管理所有 item（包括他人的）


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
ALL_ITEM_SCOPES = [
    ItemScope.READ,
    ItemScope.CREATE,
    ItemScope.UPDATE,
    ItemScope.DELETE,
    ItemScope.ADMIN,
]

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

ALL_SCOPES = ALL_ITEM_SCOPES + ALL_USER_SCOPES + ALL_SYSTEM_SCOPES


# 预定义角色对应的 scopes
# 注意：与 packages/contracts/src/scopes.ts 的 DEFAULT_ROLE_SCOPES 保持同步
DEFAULT_ROLE_SCOPES = {
    "viewer": [
        ItemScope.READ,
        UserScope.READ,
    ],
    "editor": [
        ItemScope.READ,
        ItemScope.CREATE,
        ItemScope.UPDATE,
        ItemScope.DELETE,
        UserScope.READ,
    ],
    "admin": [
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
}
