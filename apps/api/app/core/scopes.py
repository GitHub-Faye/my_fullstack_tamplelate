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
    """用户资源的权限范围"""

    READ = "user:read"       # 读取用户信息
    CREATE = "user:create"  # 创建用户
    UPDATE = "user:update"  # 更新用户信息
    DELETE = "user:delete"  # 删除用户
    ADMIN = "user:admin"    # 管理所有用户


class TaskScope(str, Enum):
    """任务资源的权限范围"""

    READ = "task:read"              # 读取任务列表/详情
    CREATE = "task:create"          # 创建任务
    UPDATE = "task:update"          # 更新任务
    DELETE = "task:delete"          # 删除任务
    ADMIN = "task:admin"            # 管理所有任务
    APPROVE = "task:approve"        # 审核任务
    CONVERT = "task:convert"        # 转换任务类型（紧急/便捷）
    REASSIGN = "task:reassign"      # 改派任务


class BidScope(str, Enum):
    """竞价报价的权限范围"""

    CREATE = "bid:create"   # 提交报价
    UPDATE = "bid:update"   # 修改报价
    READ = "bid:read"       # 查看报价列表


class ReportScope(str, Enum):
    """日报的权限范围"""

    READ = "report:read"      # 查看日报
    CREATE = "report:create"  # 填写日报
    ADMIN = "report:admin"    # 管理所有日报


class StarPointScope(str, Enum):
    """星点的权限范围"""

    READ = "starpoint:read"    # 查看自己的星点
    ADMIN = "starpoint:admin"  # 管理星点（调整、查看排行榜）


class SalaryScope(str, Enum):
    """工资的权限范围"""

    READ = "salary:read"    # 查看自己的工资试算
    ADMIN = "salary:admin"  # 管理工资（设置参数、查看汇总、导出）


class ClientResourceScope(str, Enum):
    """客资的权限范围"""

    READ = "client-resource:read"      # 查看客资
    CREATE = "client-resource:create"  # 录入客资


class RuleScope(str, Enum):
    """规则配置的权限范围"""

    ADMIN = "rule:admin"  # 管理规则配置


class DashboardScope(str, Enum):
    """Dashboard 的权限范围"""

    ENGINEER = "dashboard:engineer"  # 查看工程师仪表板
    PM = "dashboard:pm"              # 查看 PM 仪表板
    ADMIN = "dashboard:admin"        # 查看管理员仪表板


# 所有 scope 的集合（用于初始化或验证）
ALL_ITEM_SCOPES = list(ItemScope)
ALL_USER_SCOPES = list(UserScope)
ALL_TASK_SCOPES = list(TaskScope)
ALL_BID_SCOPES = list(BidScope)
ALL_REPORT_SCOPES = list(ReportScope)
ALL_STARPOINT_SCOPES = list(StarPointScope)
ALL_SALARY_SCOPES = list(SalaryScope)
ALL_CLIENT_RESOURCE_SCOPES = list(ClientResourceScope)
ALL_RULE_SCOPES = list(RuleScope)
ALL_DASHBOARD_SCOPES = list(DashboardScope)


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
    # 工程师角色权限
    "engineer": [
        TaskScope.READ,
        BidScope.CREATE,
        BidScope.UPDATE,
        ReportScope.CREATE,
        ReportScope.READ,
        StarPointScope.READ,
        SalaryScope.READ,
        DashboardScope.ENGINEER,
    ],
    # PM 角色权限
    "pm": [
        TaskScope.READ,
        TaskScope.CREATE,
        TaskScope.UPDATE,
        ReportScope.READ,
        ClientResourceScope.READ,
        ClientResourceScope.CREATE,
        SalaryScope.READ,
        DashboardScope.PM,
    ],
    # 管理员角色权限
    "admin_role": [
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
        DashboardScope.ADMIN,
    ],
}
