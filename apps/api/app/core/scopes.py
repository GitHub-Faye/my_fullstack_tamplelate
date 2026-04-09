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


# 所有 scope 的集合（用于初始化或验证）
ALL_ITEM_SCOPES = [
    ItemScope.READ,
    ItemScope.CREATE,
    ItemScope.UPDATE,
    ItemScope.DELETE,
    ItemScope.ADMIN,
]


# 预定义角色对应的 scopes
DEFAULT_ROLE_SCOPES = {
    "viewer": [
        ItemScope.READ,
    ],
    "editor": [
        ItemScope.READ,
        ItemScope.CREATE,
        ItemScope.UPDATE,
        ItemScope.DELETE,
    ],
    "admin": [
        ItemScope.READ,
        ItemScope.CREATE,
        ItemScope.UPDATE,
        ItemScope.DELETE,
        ItemScope.ADMIN,
    ],
}
