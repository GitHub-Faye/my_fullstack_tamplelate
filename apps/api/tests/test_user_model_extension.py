"""
User 模型扩展测试

测试新增的角色字段和工资字段
"""

import pytest
from app.core.models import User, UserRoleType


def test_user_role_enum_values():
    """测试用户角色枚举值"""
    assert UserRoleType.ENGINEER == "engineer"
    assert UserRoleType.PM == "pm"
    assert UserRoleType.ADMIN == "admin"


def test_user_default_role():
    """测试用户默认角色为 engineer"""
    user = User(
        email="test@example.com",
        hashed_password="hashed",
    )
    assert user.role == UserRoleType.ENGINEER


def test_user_engineer_salary_fields():
    """测试工程师工资字段"""
    user = User(
        email="engineer@example.com",
        hashed_password="hashed",
        role=UserRoleType.ENGINEER,
        S0=10000.0,
        H0=50.0,
        T_monthly_plan=160.0,
        current_starpoint=10,
    )
    assert user.S0 == 10000.0
    assert user.H0 == 50.0
    assert user.T_monthly_plan == 160.0
    assert user.current_starpoint == 10


def test_user_pm_salary_fields():
    """测试 PM 工资字段"""
    user = User(
        email="pm@example.com",
        hashed_password="hashed",
        role=UserRoleType.PM,
        S_base=5000.0,
        S_assess=3000.0,
        R_base=0.6,
        R_assess=0.4,
    )
    assert user.S_base == 5000.0
    assert user.S_assess == 3000.0
    assert user.R_base == 0.6
    assert user.R_assess == 0.4


def test_user_default_starpoint():
    """测试用户默认星点为 100"""
    user = User(
        email="test@example.com",
        hashed_password="hashed",
    )
    assert user.current_starpoint == 100


def test_user_role_can_be_changed():
    """测试用户角色可以修改"""
    user = User(
        email="test@example.com",
        hashed_password="hashed",
        role=UserRoleType.ENGINEER,
    )
    user.role = UserRoleType.PM
    assert user.role == UserRoleType.PM

    user.role = UserRoleType.ADMIN
    assert user.role == UserRoleType.ADMIN
