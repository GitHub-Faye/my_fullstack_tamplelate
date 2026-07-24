"""
工资模块数据访问层（Repository）

负责工资相关的数据库查询操作。
"""
import uuid
from typing import Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import User, TaskStatus, UserRoleType
from app.domains.salary.schemas import SalaryParamsUpdate
from app.core.db_utils import paginated_query


_SALARY_USER_FILTER = User.role.in_([UserRoleType.ENGINEER.value, UserRoleType.PM.value])


async def get_all_salaries(
    *,
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> Tuple[list[User], int]:
    """获取所有工程师和 PM 用户列表"""
    count_stmt = select(func.count()).select_from(User).where(_SALARY_USER_FILTER)
    result = await session.execute(count_stmt)
    count = result.scalar_one()

    users, count = await paginated_query(
        session=session,
        model=User,
        skip=skip,
        limit=limit,
        conditions=[_SALARY_USER_FILTER],
    )
    return users, count


async def update_user_salary_params(
    *,
    session: AsyncSession,
    user_id: uuid.UUID,
    params: SalaryParamsUpdate,
) -> Optional[User]:
    """更新用户工资参数"""
    user = await session.get(User, user_id)
    if not user:
        return None

    if user.role == UserRoleType.ENGINEER:
        if params.S0 is not None:
            user.S0 = params.S0
        if params.H0 is not None:
            user.H0 = params.H0
        if params.T_monthly_plan is not None:
            user.T_monthly_plan = params.T_monthly_plan
        if params.manual_adjustment is not None:
            user.S0 = (user.S0 or 0.0) + params.manual_adjustment
    elif user.role == UserRoleType.PM:
        if params.S_base is not None:
            user.S_base = params.S_base
        if params.S_assess is not None:
            user.S_assess = params.S_assess
        if params.R_base is not None:
            user.R_base = params.R_base
        if params.R_assess is not None:
            user.R_assess = params.R_assess
        if params.manual_adjustment is not None:
            user.S_base = (user.S_base or 0.0) + params.manual_adjustment

    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user