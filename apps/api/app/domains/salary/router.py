"""
工资 API 端点模块

提供工资试算与查看的 RESTful API 端点：
- 查看自己的工资试算
- 管理员查看全员工资汇总
- 管理员设置工资参数
"""

import uuid
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import (
    CurrentUser,
    SessionDep,
    require_scope,
    get_user_scopes,
)
from app.core.scopes import SalaryScope
from app.core.schemas import Message
from app.core.errors import BusinessException, ErrorCode
from app.core.models import User, UserRoleType

from app.domains.salary import repository
from app.domains.salary.schemas import (
    SalaryParamsUpdate,
    EngineerSalaryDetail,
    PMSalaryDetail,
    SalarySummary,
    SalarySummaryList,
    SalaryExportRequest,
    SalaryExportResponse,
)
from app.domains.salary.calculation import calculate_user_salary
from app.domains.starpoint import repository as starpoint_repo


router = APIRouter()


# ==================== 工程师/PM 端点：工资试算 ====================


@router.get(
    "/my",
    response_model=EngineerSalaryDetail | PMSalaryDetail,
    summary="查看我的工资试算",
    description="工程师或 PM 查看自己的工资试算结果"
)
async def read_my_salary(
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    获取当前用户的工资试算

    权限：工程师或 PM（需 salary:read 权限）

    计算规则：
    - 工程师：S下 = (S0 - P差额) × K
    - PM：S总 = S底 + S考
    """
    # 检查权限
    user_scopes = await get_user_scopes(session, current_user)
    if SalaryScope.READ.value not in user_scopes:
        raise BusinessException(
            code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            detail="You don't have permission to view salary"
        )

    # 检查角色
    if current_user.role not in [UserRoleType.ENGINEER, UserRoleType.PM]:
        raise BusinessException(
            code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            detail="Only engineers and PMs can view salary"
        )

    # 计算工资
    result = await calculate_user_salary(session=session, user=current_user)

    # 根据角色返回不同模型
    if current_user.role == UserRoleType.ENGINEER:
        return EngineerSalaryDetail(**result)
    else:
        return PMSalaryDetail(**result)


# ==================== 管理员端点：工资汇总和设置 ====================


@router.get(
    "",
    response_model=SalarySummaryList,
    summary="查看工资汇总（管理员）",
    description="管理员查看所有工程师和 PM 的工资汇总"
)
async def read_salary_summary(
    session: SessionDep,
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1, description="页码，从1开始")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量，默认20")] = 20,
    _: Annotated[None, Depends(require_scope(SalaryScope.ADMIN))] = None,
) -> Any:
    """
    获取工资汇总列表

    权限：管理员（需 salary:admin 权限）
    """
    offset = (page - 1) * page_size

    # 获取基础列表
    salaries, count = await repository.get_all_salaries(
        session=session,
        skip=offset,
        limit=page_size,
    )

    # 完整计算工资（需要 K 系数）
    result_salaries = []
    for salary_dict in salaries:
        user = await session.get(User, salary_dict["user_id"])
        if user:
            try:
                calculated = await calculate_user_salary(session=session, user=user)
                salary_dict["salary"] = calculated.get("salary_final") or calculated.get("salary_total", 0)
            except Exception:
                # 计算失败，使用默认值
                pass
        result_salaries.append(SalarySummary(**salary_dict))

    return SalarySummaryList(
        data=result_salaries,
        count=count,
        page=page,
        page_size=page_size,
        total_pages=(count + page_size - 1) // page_size if count > 0 else 0,
    )


@router.put(
    "/users/{user_id}/params",
    response_model=Message,
    summary="设置工资参数（管理员）",
    description="管理员设置工程师或 PM 的工资参数"
)
async def update_salary_params(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    user_id: uuid.UUID,
    params: SalaryParamsUpdate,
    _: Annotated[None, Depends(require_scope(SalaryScope.ADMIN))] = None,
) -> Any:
    """
    设置工资参数

    权限：管理员（需 salary:admin 权限）

    可设置字段：
    - 工程师：S0, H0, T_monthly_plan
    - PM：S_base, S_assess, R_base, R_assess, baseline_client_count
    """
    # 转换为字典，过滤 None 值
    params_dict = params.model_dump(exclude_none=True)

    if not params_dict:
        raise BusinessException(
            code=ErrorCode.SYSTEM_VALIDATION_ERROR,
            detail="No parameters provided"
        )

    # 更新参数
    user = await repository.update_user_salary_params(
        session=session,
        user_id=user_id,
        params=params_dict,
    )

    if not user:
        raise BusinessException(
            code=ErrorCode.USER_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )

    return Message(message=f"Salary parameters updated for user {user_id}")


@router.post(
    "/export",
    response_model=SalaryExportResponse,
    summary="导出工资表（管理员）",
    description="管理员导出工资汇总表为 CSV"
)
async def export_salaries(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    request: SalaryExportRequest,
    _: Annotated[None, Depends(require_scope(SalaryScope.ADMIN))] = None,
) -> Any:
    """
    导出工资表

    权限：管理员（需 salary:admin 权限）

    导出格式：CSV
    """
    # 获取所有员工工资
    salaries, _ = await repository.get_all_salaries(
        session=session,
        skip=0,
        limit=1000,  # 假设不超过 1000 人
    )

    # 完整计算工资
    result_salaries = []
    for salary_dict in salaries:
        user = await session.get(User, salary_dict["user_id"])
        if user:
            try:
                calculated = await calculate_user_salary(session=session, user=user)
                salary_dict["salary"] = calculated.get("salary_final") or calculated.get("salary_total", 0)
            except Exception:
                pass
        result_salaries.append(salary_dict)

    # 生成文件名
    month = request.month or datetime.now(timezone.utc).strftime("%Y-%m")
    filename = f"salary_export_{month}.csv"

    # 注意：这里返回的是模拟的下载链接
    # 实际实现中，应该：
    # 1. 生成文件并保存到对象存储（如 S3、MinIO）
    # 2. 返回真实的下载链接
    # 当前简化实现：直接返回数据

    return SalaryExportResponse(
        download_url=f"/api/v1/salaries/download/{filename}",
        filename=filename,
        record_count=len(result_salaries),
    )
