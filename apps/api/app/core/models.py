# app/core/models.py   （或你当前的文件）

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional   # 保留 typing.List

from pydantic import EmailStr
from sqlalchemy import DateTime, ForeignKey
from sqlmodel import Field, Relationship, SQLModel


def get_datetime_utc() -> datetime:
    """返回 UTC 时间，用于默认 created_at 字段。"""
    return datetime.now(timezone.utc)


# ==================================== 任务状态枚举 ====================================

class TaskStatus(str, Enum):
    """
    任务状态枚举

    状态流转：
    unconfirmed -> confirmed_unpublished -> bidding -> pending_start -> in_progress -> completed
    中间状态：paused（可从 in_progress 暂停）
    """
    UNCONFIRMED = "unconfirmed"                      # 未确认（PM提交，待管理员审核）
    CONFIRMED_UNPUBLISHED = "confirmed_unpublished"  # 已确认未发布（管理员审核通过，待发布）
    BIDDING = "bidding"                              # 竞价中
    PENDING_START = "pending_start"                  # 待开工
    IN_PROGRESS = "in_progress"                      # 进行中
    PAUSE_REQUESTED = "pause_requested"              # 暂停待审批（工程师申请，待管理员审批）
    PAUSED = "paused"                                # 暂停中（管理员审批通过）
    COMPLETED = "completed"                          # 已完成


class TaskType(str, Enum):
    """
    任务类型枚举

    - normal: 正常任务，按标准竞价流程
    - urgent: 紧急任务，优先竞价
    - convenient: 便捷任务，不参与竞价，按需执行
    """
    NORMAL = "normal"
    URGENT = "urgent"
    CONVENIENT = "convenient"


class ReportStage(str, Enum):
    """
    日报阶段枚举

    - developing: 开发中
    - testing: 测试中
    - completed: 已完成
    - paused: 暂停中
    """
    DEVELOPING = "developing"
    TESTING = "testing"
    COMPLETED = "completed"
    PAUSED = "paused"


class JudgmentType(str, Enum):
    """
    星点判定类型枚举

    - manual: 手动判定（管理员手动调整）
    - auto_ratio: 按比例自动判定
    - auto_threshold: 按阈值自动判定
    """
    MANUAL = "manual"
    AUTO_RATIO = "auto_ratio"
    AUTO_THRESHOLD = "auto_threshold"


class RuleCategory(str, Enum):
    """
    规则分类枚举

    - starpoint_reward: 星点奖励规则
    - salary_formula: 工资计算公式
    - client_resource: 客资相关参数
    - completion_judgment: 完成判定规则
    - system_param: 系统参数
    """
    STARPOINT_REWARD = "starpoint_reward"
    SALARY_FORMULA = "salary_formula"
    CLIENT_RESOURCE = "client_resource"
    COMPLETION_JUDGMENT = "completion_judgment"
    SYSTEM_PARAM = "system_param"


# ==================================== UserRole (Association Table) ====================================
# 必须在 Role 和 User 之前定义，因为它们都引用了这个类

class UserRole(SQLModel, table=True):
    """用户与角色的多对多关联表"""
    user_id: uuid.UUID = Field(
        foreign_key="user.id",
        primary_key=True,
        ondelete="CASCADE",
    )
    role_id: uuid.UUID = Field(
        foreign_key="role.id",
        primary_key=True,
        ondelete="CASCADE",
    )


# ==================================== 角色类型枚举 ====================================
from enum import Enum


class UserRoleType(str, Enum):
    """
    用户角色类型枚举

    三种角色完全独立，不支持兼任：
    - engineer: 工程师，参与竞价报价、执行任务、填报日报
    - pm: 市场产品PM，发布任务需求、管理客资数据
    - admin: 管理员，审核任务、管理工资与规则
    """
    ENGINEER = "engineer"
    PM = "pm"
    ADMIN = "admin"


# ==================================== Role ====================================

class RoleBase(SQLModel):
    name: str = Field(unique=True, index=True, max_length=50)


class Role(RoleBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: Optional[datetime] = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )

    # 与 User 的多对多关系（通过 UserRole 关联表）
    users: List["User"] = Relationship(
        back_populates="roles",
        link_model=UserRole,
    )
    # 与 RoleScope 的一对多关系
    scopes: List["RoleScope"] = Relationship(
        back_populates="role",
        cascade_delete=True,
    )


# ==================================== RoleScope ====================================

class RoleScopeBase(SQLModel):
    scope: str = Field(max_length=100)  # 如 "item:read", "item:create"


class RoleScope(RoleScopeBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    role_id: uuid.UUID = Field(
        foreign_key="role.id", nullable=False, ondelete="CASCADE"
    )
    created_at: Optional[datetime] = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )

    # 与 Role 的多对一关系
    role: Optional["Role"] = Relationship(back_populates="scopes")


# ==================================== User ====================================
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: Optional[str] = Field(default=None, max_length=255)
    # 用户角色：engineer | pm | admin（完全独立，不支持兼任）
    role: UserRoleType = Field(default=UserRoleType.ENGINEER)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: Optional[datetime] = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )

    # ==================== 工程师工资字段 ====================
    # S0: 月度工资基数
    S0: Optional[float] = Field(default=None, ge=0)
    # H0: 基准时薪，由管理员手动设置
    H0: Optional[float] = Field(default=None, ge=0)
    # T_monthly_plan: 月度计划工时
    T_monthly_plan: Optional[float] = Field(default=None, ge=0)
    # current_starpoint: 当前星点总数
    current_starpoint: int = Field(default=0)

    # ==================== PM 工资字段 ====================
    # S_base: 底薪
    S_base: Optional[float] = Field(default=None, ge=0)
    # S_assess: 考核部分
    S_assess: Optional[float] = Field(default=None, ge=0)
    # R_base: 底薪比例
    R_base: Optional[float] = Field(default=None, ge=0, le=1)
    # R_assess: 考核比例
    R_assess: Optional[float] = Field(default=None, ge=0, le=1)

    # ==================== PM 客资字段 ====================
    # baseline_client_count: 基准客资数（L基）
    baseline_client_count: Optional[int] = Field(default=None, ge=0)
    created_at: Optional[datetime] = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )

    # 与 Item 的一对多关系
    items: List["Item"] = Relationship(
        back_populates="owner",
        cascade_delete=True,          # 推荐，替代 cascade="all, delete-orphan"
    )
    # 与 Role 的多对多关系（通过 UserRole 关联表）
    roles: List["Role"] = Relationship(
        back_populates="users",
        link_model=UserRole,
    )


# ==================================== Item ====================================
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=255)


class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: Optional[datetime] = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )

    # 关键修改在这里
    owner: Optional["User"] = Relationship(back_populates="items")


# ==================================== Task ====================================
class TaskBase(SQLModel):
    """任务基础模型"""
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    progress: Optional[str] = Field(default=None, max_length=5000, description="工程师日报进度描述（与 description 分离，不污染 PM 原始描述）")
    task_type: TaskType = Field(default=TaskType.NORMAL)
    status: TaskStatus = Field(default=TaskStatus.UNCONFIRMED)
    T_reported: Optional[float] = Field(default=None, ge=0, description="T报（工程师填报工时）")
    T_actual: Optional[float] = Field(default=None, ge=0, description="T实（实际结算工时）")
    expected_online_time: Optional[datetime] = Field(default=None, sa_type=DateTime(timezone=True), description="预期上线时间")
    T_reported_complete_time: Optional[datetime] = Field(default=None, sa_type=DateTime(timezone=True), description="T报完成上报时间")


class Task(TaskBase, table=True):
    """任务模型"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # 关联关系
    pm_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        description="发布任务的PM ID"
    )
    engineer_id: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="user.id",
        description="被分配的工程师ID"
    )

    # 竞价截止时间
    bidding_deadline: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        description="竞价截止时间"
    )

    # 时间戳
    created_at: Optional[datetime] = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
    updated_at: Optional[datetime] = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": get_datetime_utc}
    )

    # 非持久化字段：用于 API 响应中展示关联用户姓名
    pm_name: Optional[str] = Field(default=None, sa_column=None, description="发布人姓名（非持久化）")
    engineer_name: Optional[str] = Field(default=None, sa_column=None, description="工程师姓名（非持久化）")

    # 关系
    pm: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Task.pm_id]"}
    )
    engineer: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Task.engineer_id]"}
    )
    bids: List["Bid"] = Relationship(back_populates="task", cascade_delete=True)
    attachments: List["Attachment"] = Relationship(back_populates="task", cascade_delete=True)


# ==================================== Bid ====================================
class BidBase(SQLModel):
    """竞价基础模型"""
    T_reported: float = Field(ge=0, description="工程师报价工时")
    amount: float = Field(ge=0, description="竞价金额")


class Bid(BidBase, table=True):
    """竞价模型"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # 关联关系
    task_id: uuid.UUID = Field(
        foreign_key="task.id",
        nullable=False,
        ondelete="CASCADE"
    )
    engineer_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False
    )

    # 时间戳
    created_at: Optional[datetime] = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
    updated_at: Optional[datetime] = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": get_datetime_utc}
    )

    # 关系
    task: Optional["Task"] = Relationship(back_populates="bids")
    engineer: Optional["User"] = Relationship()


# ==================================== Attachment ====================================
class AttachmentBase(SQLModel):
    """附件基础模型"""
    file_name: str = Field(max_length=255)
    file_path: str = Field(max_length=500)
    file_size: int = Field(ge=0, description="文件大小（字节）")


class Attachment(AttachmentBase, table=True):
    """附件模型"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # 关联关系
    task_id: uuid.UUID = Field(
        foreign_key="task.id",
        nullable=False,
        ondelete="CASCADE"
    )
    uploaded_by: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False
    )

    # 时间戳
    created_at: Optional[datetime] = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )

    # 关系
    task: Optional["Task"] = Relationship(back_populates="attachments")
    uploader: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Attachment.uploaded_by]"}
    )


# ==================================== DailyReport ====================================
class DailyReportBase(SQLModel):
    """日报基础模型"""
    today_hours: float = Field(ge=0, description="今日工作时长（小时）")
    current_stage: ReportStage = Field(description="当前阶段")
    progress: Optional[str] = Field(default=None, max_length=500, description="进度描述")
    completion_judgment: Optional[str] = Field(default=None, max_length=500, description="完成判定说明")
    starpoint_change: Optional[int] = Field(default=0, description="星点变化量")
    notes: Optional[str] = Field(default=None, max_length=1000, description="备注说明")
    summary: Optional[str] = Field(default=None, max_length=1000, description="工作总结")
    has_blocker: bool = Field(default=False, description="是否有阻塞问题")


class DailyReport(DailyReportBase, table=True):
    """日报模型"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # 关联关系
    engineer_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        description="填报工程师ID"
    )
    task_id: uuid.UUID = Field(
        foreign_key="task.id",
        nullable=False,
        description="关联任务ID"
    )

    # 报告日期
    report_date: datetime = Field(
        sa_type=DateTime(timezone=True),
        description="报告日期"
    )

    # 时间戳
    created_at: Optional[datetime] = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )

    # 关系
    engineer: Optional["User"] = Relationship()
    task: Optional["Task"] = Relationship()


# ==================================== StarPoint Record ====================================
class StarPointRecordBase(SQLModel):
    """星点记录基础模型"""
    change_amount: int = Field(description="星点变化量（可正可负）")
    reason: Optional[str] = Field(default=None, max_length=500, description="变化原因")
    judgment_type: JudgmentType = Field(description="判定类型")
    T_reported: Optional[float] = Field(default=None, ge=0, description="报价工时")
    T_actual: Optional[float] = Field(default=None, ge=0, description="实际工时")


class StarPointRecord(StarPointRecordBase, table=True):
    """星点记录模型"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # 关联关系
    engineer_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        description="工程师ID"
    )
    task_id: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="task.id",
        description="关联任务ID（可为空，如手动调整）"
    )

    # 时间戳
    created_at: Optional[datetime] = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )

    # 关系
    engineer: Optional["User"] = Relationship()
    task: Optional["Task"] = Relationship()


# ==================================== ClientResource ====================================
class ClientResourceBase(SQLModel):
    """客资基础模型"""
    actual_count: int = Field(ge=0, description="实际客资数")
    baseline_count: int = Field(ge=0, description="基准客资数")


class ClientResource(ClientResourceBase, table=True):
    """客资模型"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # 关联关系
    pm_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        description="PM ID"
    )

    # 记录日期
    date: datetime = Field(
        sa_type=DateTime(timezone=True),
        description="记录日期"
    )

    # 时间戳
    created_at: Optional[datetime] = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )

    # 关系
    pm: Optional["User"] = Relationship()


# ==================================== SystemRule ====================================
class SystemRuleBase(SQLModel):
    """系统规则基础模型"""
    category: RuleCategory = Field(description="规则分类")
    name: str = Field(max_length=100, description="规则名称")
    applies_to: Optional[str] = Field(default=None, max_length=50, description="适用对象（如角色类型）")
    value: str = Field(max_length=500, description="规则值（JSON 或数值）")
    is_public: bool = Field(default=False, description="是否对员工公开")
    is_active: bool = Field(default=True, description="是否启用")


# ==================================== AuditLog ====================================

class AuditLogBase(SQLModel):
    """操作审计日志基础模型"""
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, description="操作人ID")
    action: str = Field(max_length=100, description="操作类型（如 user.create, user.toggle_active）")
    target_type: str = Field(max_length=50, description="操作对象类型（如 user, task）")
    target_id: Optional[str] = Field(default=None, max_length=100, description="操作对象ID")
    details: Optional[str] = Field(default=None, max_length=2000, description="操作详情（JSON 格式）")
    ip_address: Optional[str] = Field(default=None, max_length=50, description="操作IP")


class AuditLog(AuditLogBase, table=True):
    """操作审计日志模型"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    created_at: Optional[datetime] = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )

    # 关系
    operator: Optional["User"] = Relationship()


class SystemRule(SystemRuleBase, table=True):
    """系统规则模型"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # 时间戳
    created_at: Optional[datetime] = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
    updated_at: Optional[datetime] = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": get_datetime_utc}
    )

