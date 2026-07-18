"""
工资 API 端点模块

提供工资试算与查看的 RESTful API 端点：
- 查看自己的工资试算
- 管理员查看全员工资汇总
- 管理员设置工资参数
- 管理员导出工资表（CSV）
"""

import csv
import io
import uuid
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.core.dependencies import (
    CurrentUser,
    SessionDep,
    require_scope,
)
from app.core.scopes import SalaryScope
from app.core.schemas import Message
from app.core.errors import BusinessException, ErrorCode
from app.core.models import User

from app.domains.salary import repository
from app.domains.salary.schemas import (
    SalaryParamsUpdate,
    EngineerSalaryDetail,
    PMSalaryDetail,
    SalarySummary,
    SalarySummaryList,
    SalaryExportRequest,
)
from app.domains.salary.calculation import calculate_user_salary


router = APIRouter()


# ==================== 辅助函数 ====================

async def _calculate_salaries(
    session: SessionDep,
    users: list[User],
) -> list[SalarySummary]:
    """
    批量计算用户工资，返回 SalarySummary 列表

    遍历用户调用 calculate_user_salary，捕获 BusinessException 异常。
    """
    result = []
    for user in users:
        try:
            calculated = await calculate_user_salary(session=session, user=user)
            salary = calculated.salary_final if isinstance(calculated, EngineerSalaryDetail) else calculated.salary_total
        except BusinessException:
            salary = 0.0

        result.append(SalarySummary(
            user_id=user.id,
            full_name=user.full_name,
            role=user.role.value,
            salary=salary,
        ))
    return result


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
    _: Annotated[None, Depends(require_scope(SalaryScope.READ))] = None,
) -> Any:
    """
    获取当前用户的工资试算

    权限：工程师或 PM（需 salary:read 权限）
    require_scope 已确保权限，calculate_user_salary 内部校验角色。

    计算规则：
    - 工程师：S下 = (S0 - P差额) × K
    - PM：S总 = S底 + S考
    """
    return await calculate_user_salary(session=session, user=current_user)


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

    # 获取用户列表
    users, count = await repository.get_all_salaries(
        session=session,
        skip=offset,
        limit=page_size,
    )

    # 计算工资
    result_salaries = await _calculate_salaries(session, users)

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
    if not params.model_dump(exclude_none=True):
        raise BusinessException(
            code=ErrorCode.SYSTEM_VALIDATION_ERROR,
            detail="No parameters provided"
        )

    # 更新参数（直接传入 typed DTO，按角色过滤字段）
    user = await repository.update_user_salary_params(
        session=session,
        user_id=user_id,
        params=params,
    )

    if not user:
        raise BusinessException(
            code=ErrorCode.USER_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )

    return Message(message=f"Salary parameters updated for user {user_id}")


@router.post(
    "/export",
    summary="导出工资表（管理员）",
    description="管理员导出全员工资汇总表为 CSV 文件流"
)
async def export_salaries(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    request: SalaryExportRequest,
    _: Annotated[None, Depends(require_scope(SalaryScope.ADMIN))] = None,
) -> Any:
    """
    导出工资表为 CSV

    权限：管理员（需 salary:admin 权限）
    """
    # 获取所有员工
    users, _ = await repository.get_all_salaries(
        session=session,
        skip=0,
        limit=1000,
    )

    # 计算每个员工的工资并生成 CSV
    result_salaries = await _calculate_salaries(session, users)
    rows = []
    for s in result_salaries:
        rows.append({
            "user_id": str(s.user_id),
            "full_name": s.full_name or "",
            "role": s.role,
            "salary": round(s.salary, 2),
        })

    # 生成 CSV
    month = request.month or datetime.now(timezone.utc).strftime("%Y-%m")
    filename = f"salary_export_{month}.csv"

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["user_id", "full_name", "role", "salary"])
    writer.writeheader()
    writer.writerows(rows)
    csv_content = output.getvalue()

    headers = {
        "Content-Disposition": f"attachment; filename=\"{filename}\"",
    }
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers=headers,
    )
