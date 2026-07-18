"""
数据概览 API 端点模块

提供三端首页数据概览 API：
- GET /dashboard/engineer - 工程师工作台首页
- GET /dashboard/pm - PM 工作台首页
- GET /dashboard/admin - 管理端数据概览
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.core.dependencies import (
    CurrentUser,
    SessionDep,
    require_scope,
)
from app.core.scopes import DashboardScope
from app.core.models import User, UserRoleType

from app.domains.dashboard import repository
from app.domains.salary import repository as salary_repo
from app.domains.salary.calculation import calculate_user_salary
from app.domains.salary.schemas import EngineerSalaryDetail, PMSalaryDetail


router = APIRouter()


def _get_salary_preview(salary_data: EngineerSalaryDetail | PMSalaryDetail) -> float:
    """从工资试算结果中提取预览金额"""
    if isinstance(salary_data, EngineerSalaryDetail):
        return salary_data.salary_final
    return salary_data.salary_total


@router.get(
    "/engineer",
    summary="工程师工作台首页",
    description="工程师查看自己的工作指标：当前星点、本月剩余工时、收入试算、T报准确率"
)
async def read_engineer_dashboard(
    session: SessionDep,
    current_user: CurrentUser,
    _: Annotated[None, Depends(require_scope(DashboardScope.ENGINEER))] = None,
) -> Any:
    """
    获取工程师仪表板数据

    权限：工程师（需 dashboard:engineer 权限）
    """
    salary_data = await calculate_user_salary(session=session, user=current_user)
    salary_preview = _get_salary_preview(salary_data)

    return await repository.get_engineer_dashboard(
        session=session,
        engineer=current_user,
        salary_preview=salary_preview,
    )


@router.get(
    "/pm",
    summary="PM 工作台首页",
    description="PM 查看自己的工作指标：今日新增客资、本月新增客资、收入试算"
)
async def read_pm_dashboard(
    session: SessionDep,
    current_user: CurrentUser,
    _: Annotated[None, Depends(require_scope(DashboardScope.PM))] = None,
) -> Any:
    """
    获取 PM 仪表板数据

    权限：PM（需 dashboard:pm 权限）
    """
    salary_data = await calculate_user_salary(session=session, user=current_user)
    salary_preview = _get_salary_preview(salary_data)

    return await repository.get_pm_dashboard(
        session=session,
        pm=current_user,
        salary_preview=salary_preview,
    )


@router.get(
    "/admin",
    summary="管理端数据概览",
    description="管理员查看全系统数据概览：客资、日志、任务、工程师负载、星点排行榜、收入统计"
)
async def read_admin_dashboard(
    session: SessionDep,
    current_user: CurrentUser,
    _: Annotated[None, Depends(require_scope(DashboardScope.ADMIN))] = None,
) -> Any:
    """
    获取管理员仪表板数据

    权限：管理员（需 dashboard:admin 权限）
    """
    # 获取所有工程师和 PM 用户列表
    users, _ = await salary_repo.get_all_salaries(session=session, skip=0, limit=1000)

    # 计算每个用户的工资（使用完整工资计算）
    engineer_cost = 0.0
    pm_cost = 0.0

    for user in users:
        try:
            salary_data = await calculate_user_salary(session=session, user=user)
            amount = _get_salary_preview(salary_data)
            if user.role == UserRoleType.ENGINEER:
                engineer_cost += amount
            else:
                pm_cost += amount
        except Exception:
            continue

    total_salary = engineer_cost + pm_cost

    return await repository.get_admin_dashboard(
        session=session,
        total_salary=round(total_salary, 2),
        engineer_salary_cost=round(engineer_cost, 2),
        pm_salary_cost=round(pm_cost, 2),
    )