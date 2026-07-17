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
    PAUSED = "paused"                                # 已暂停
    COMPLETED = "completed"                          # 已完成


class TaskType(str, Enum):
    """
    任务类型枚举

    - normal: 普通任务，按标准竞价流程
    - urgent: 紧急任务，优先竞价
    - convenient: 便捷任务，不参与竞价，按需执行
    """
    NORMAL = "normal"
    URGENT = "urgent"
    CONVENIENT = "convenient"


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
    task_type: TaskType = Field(default=TaskType.NORMAL)
    status: TaskStatus = Field(default=TaskStatus.UNCONFIRMED)
    T_reported: Optional[float] = Field(default=None, ge=0, description="工程师填报工时")
    T_actual: Optional[float] = Field(default=None, ge=0, description="实际结算工时")


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

